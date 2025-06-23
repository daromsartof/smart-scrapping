import asyncio
from typing import List, Dict, Any, Optional
import logging
from services.scraping_service import WebScrapingTool
from services.agent_service import create_llm
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
from langchain.prompts import ChatPromptTemplate

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_scraping_tool(config: Dict[str, Any]) -> WebScrapingTool:
    """Create configured web scraping tool"""
    return WebScrapingTool(max_content_length=config["max_scrape_length"])


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
        "llm_max_tokens": get_int_env("LLM_MAX_TOKENS", 3000),
        "request_timeout": get_int_env("REQUEST_TIMEOUT", 30),
        "llm_timeout": get_int_env("LLM_TIMEOUT", 60),
    }
    
async def main(): 
    try:
        scraping_tool = create_scraping_tool({"max_scrape_length": 200000})
        user_prompt = "lister tous les biens en encore en vente"
        
        # Await the async scrape
        html = await scraping_tool._arun(url="https://gary.ch/acheter")
        
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

        print(response.content)

    except Exception as e:
        print("Error:", str(e))
        
        
        
if __name__ == "__main__":
    asyncio.run(main())