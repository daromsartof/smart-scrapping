

import logging
from langchain_google_genai import ChatGoogleGenerativeAI

from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_llm(config: Dict[str, Any]) -> ChatGoogleGenerativeAI:
    """Initialize Gemini model with configuration"""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=config["google_api_key"],
        temperature=config["llm_temperature"],
        max_tokens=config["llm_max_tokens"],
        timeout=config["llm_timeout"],
    )
