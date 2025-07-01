import asyncio
from typing import List, Dict, Any, Optional
import logging
from services.scraping_service import WebScrapingTool
from services.agent_service import create_llm
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
from langchain.prompts import ChatPromptTemplate
import uuid
import json
import re
        
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from IPython.display import Image, display


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class State(TypedDict):
    data: List      # everything we’ve scraped so far
    next_url: Optional[str]         # URL of the next page, or None
    page_idx: int                   # 1‑based page counter
    page_limit: int

def create_scraping_tool(config: Dict[str, Any]) -> WebScrapingTool:
    """Create configured web scraping tool"""
    return WebScrapingTool()


def get_int_env(key: str, default: int) -> int:
    """Parse integer from environment variable with fallback"""
    try:
        return int(os.getenv(key, default))
    except ValueError:
        logger.warning(f"Invalid {key}, using default: {default}")
        return default

def get_float_env(key: str, default: float) -> float:
    """Parse float from environment variable with fallback"""
    try:
        return float(os.getenv(key, default))
    except ValueError:
        logger.warning(f"Invalid {key}, using default: {default}")
        return default

def validate_api_keys():
    """Validate required API keys are present"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key or google_api_key == "your_google_api_key_here":
        raise ValueError("GOOGLE_API_KEY environment variable is required")

    return google_api_key

def build_config() -> Dict[str, Any]:
    """Build configuration from environment variables"""
    google_api_key = validate_api_keys()
    return {
        "google_api_key": google_api_key,
        "llm_temperature": get_float_env("LLM_TEMPERATURE", 0.1),
        "llm_max_tokens": get_int_env("LLM_MAX_TOKENS", 30000),
        "request_timeout": get_int_env("REQUEST_TIMEOUT", 30),
        "llm_timeout": get_int_env("LLM_TIMEOUT", 60),
    }
    
async def get_page_data(state: State) -> State: 
    """
    ① scrape + ② extract items + ③ find link to the next page
    Return the *delta* you want to merge into the global state.
    """
    try:
        scraping_tool = create_scraping_tool({"max_scrape_length": 200000})
        user_prompt = """
            Lister danse un tableau de json tous les liens des imobiliers de l'agence, avec les champs suivants: 
                'id' : c'est l'identifiant du bien, 
                'nom' : c'est le nom du bien, 
                'url': c'est l'url du bien,
                'image_url': l'url de l'image du bien,
                'status': vendu ou a louer ou a vendre
        """
        print("state['next_url'] ", state['next_url'])
        # Await the async scrape
        html = await scraping_tool._arun(url=state['next_url'])
        
        # Build config and initialize LLM
        config = build_config()
        llm = create_llm(config=config)

        # Load README.md content as system prompt
        with open("./prompt/web_scraping.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Construct the full prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", content),
            ("human", f"user_query: {user_prompt}\nhtml_content: {html}")
        ])

        # Use the prompt + LLM pipeline
        chain = prompt | llm
        response = await chain.ainvoke({
            "user_prompt": user_prompt,
            "html": html
        })

        with open(f"output_test-26-06-{str(uuid.uuid4())}.json", "w") as f:
            f.write(response.content)
            
        clean_json = re.sub(r"```[\w]*\s*|\s*```$", "", response.content).strip()
        
        data_json = json.loads(clean_json)
        return {
            "data": data_json['data'],
            "next_url": data_json['next_url'],  
            "page_idx": state["page_idx"] + 1,
        }
    except Exception as e:
        print(e)
        return {
            "data": [],
            "next_url": None,
            "page_idx": 1,
        }
    

def accumulate(old: State, delta: State) -> State:
    """Merge the newly‑scraped items into the running state."""
    return {
        "data": old["data"] + delta["data"],
        "next_url": delta["next_url"],
        "page_idx": delta["page_idx"],
    }
    
def should_continue(state: State) -> str:
    """
    Return *the name of the next node*.
    Anything truthy in `next_url` → keep looping,
    otherwise jump to END.
    """
    reached_cap = state["page_idx"] > state["page_limit"]
    has_more    = bool(state["next_url"])
    return "get_page_data" if has_more and not reached_cap else "END"
        
async def main():
    url = "https://www.dynasty-immobilier.ch/acheter"
    page_limit = 3
    init_state = {
        "data": [],
        "next_url": url,
        "page_idx": 1,
        "page_limit": page_limit,
    }
    
   
    index = 1
    data = []
    #reponse = await get_page_data(url)
    builder = StateGraph(State)
    builder.add_node("get_page_data", get_page_data, accumulator=accumulate)
    
    builder.add_edge(START, "get_page_data")
    builder.add_conditional_edges("get_page_data", should_continue,  { 
        "get_page_data": "get_page_data",
        "END": END
    })
    builder.add_edge("get_page_data" , END)
    graph = builder.compile()

    with open("graph.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    print("Saved to graph.png – open it with any image viewer")
    final = await graph.ainvoke(init_state)
    print(final)
    if final["next_url"] is None:
        reason = "no more pages"
    else:
        reason = f"page limit {final['page_limit']} reached"

    print(
        f"Scraped {len(final['data'])} items in {final['page_idx']-1} pages "
        f"({reason})."
    )

if __name__ == "__main__":
    asyncio.run(main())