from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
import main

app = FastAPI()

class ScrapeRequest(BaseModel):
    url: str
    page_limit: Optional[int] = 3

@app.post("/scrape")
async def scrape(request: ScrapeRequest):
    # Prepare initial state as in main.py
    init_state = {
        "data": [],
        "next_url": request.url,
        "page_idx": 1,
        "page_limit": request.page_limit or 3,
    }
    graph = main.graph_constuct()
    
    final = await graph.ainvoke(init_state)
    return {"data": final["data"], "pages": final["page_idx"] - 1}

@app.get("/health")
def health():
    return {"status": "ok"} 

