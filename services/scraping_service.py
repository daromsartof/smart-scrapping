"""
Web scraping tool using Chromium for dynamic content extraction
"""

import logging
import asyncio
from typing import List, Type

from pydantic import BaseModel, Field, ConfigDict
from langchain.tools import BaseTool
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_default_tags() -> List[str]:
    """Get default HTML tags for web scraping"""
    return ["p", "li", "div", "a", "span", "h1", "h2", "h3", "h4", "h5", "h6"]


class WebScrapingInput(BaseModel):
    url: str = Field(description="URL to scrape")
    tags_to_extract: List[str] = Field(
        default_factory=get_default_tags, description="HTML tags to extract"
    )


class WebScrapingTool(BaseTool):
    """Scrape websites when search results are insufficient"""

    name: str = "scrape_website"
    description: str = """Scrape complete website content using Chromium browser for comprehensive page extraction.

    REQUIRED PARAMETERS:
    - url (string): Complete URL to scrape (must include https:// or http://)

    OPTIONAL PARAMETERS:
    - tags_to_extract (list): HTML tags to extract content from 
      Default: ["p", "li", "div", "a", "span", "h1", "h2", "h3", "h4", "h5", "h6"]
      Custom examples: ["pre", "code"] for code examples, ["table", "tr", "td"] for tables

    WHEN TO USE:
    - Search results are incomplete or insufficient
    - Need complete page content including code examples
    - Page has dynamic JavaScript content that search missed
    - Need specific formatting or structure that search doesn't capture

    EXAMPLES:
    - Basic scraping: url="https://docs.langchain.com/docs/modules/agents"
    - Code-focused scraping: url="https://fastapi.tiangolo.com/tutorial/", tags_to_extract=["pre", "code", "p"]
    - Table extraction: url="https://docs.python.org/3/library/", tags_to_extract=["table", "tr", "td", "th"]

    BEST PRACTICES:
    - Only use after search_documentation provides insufficient information
    - Prefer URLs from previous search results for relevance
    - Use specific tag extraction for targeted content (faster processing)
    - Be aware: ~3-10x slower than search, use sparingly for performance

    LIMITATIONS:
    - Content truncated at configured limit to prevent excessive token usage
    - Some sites may block automated scraping
    - Slower than search - reserve for when search is inadequate
    """
    args_schema: Type[BaseModel] = WebScrapingInput

    max_content_length: int = Field(default=20000, exclude=True)
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Add memory for last scraped content
    last_scraped_content: str = None

    def __init__(self, max_content_length: int = 20000):
        super().__init__(
            max_content_length=max_content_length, args_schema=WebScrapingInput
        )
        self.last_scraped_content = None

    async def _process_scraping(
        self, url: str, tags_to_extract: List[str] = None, is_async: bool = True
    ) -> str:
        """Common logic for both sync and async scraping"""
        try:
            if tags_to_extract is None:
                tags_to_extract = get_default_tags()

            loader = AsyncChromiumLoader([url])

            if is_async:
                html_docs = await asyncio.to_thread(loader.load)
            else:
                html_docs = loader.load()

            if not html_docs:
                return f"Failed to load content from {url}"

            bs_transformer = BeautifulSoupTransformer()

            if is_async:
                docs_transformed = await asyncio.to_thread(
                    bs_transformer.transform_documents,
                    html_docs,
                    tags_to_extract=tags_to_extract,
                )
            else:
                docs_transformed = bs_transformer.transform_documents(
                    html_docs,
                    tags_to_extract=tags_to_extract,
                )

            if not docs_transformed:
                return f"No content extracted from {url}"

            content = docs_transformed[0].page_content
        
            if len(content) > self.max_content_length:
                content = (
                    content[: self.max_content_length] + "\n\n... (content truncated)"
                )

            # Store the truncated content in memory for agent access
            self.last_scraped_content = content

            return f"""
**Website Scraped:** {url}
**Content Extracted:**

{content}

**Note:** Complete website content for comprehensive analysis.
"""

        except Exception as e:
            return f"Web scraping error for {url}: {str(e)}"

    def _run(self, url: str, tags_to_extract: List[str] = None) -> str:
        """Scrape website content"""
        return asyncio.run(
            self._process_scraping(url, tags_to_extract, is_async=False)
        )

    async def _arun(self, url: str, tags_to_extract: List[str] = None) -> str:
        """Async version of scraping"""
        return await self._process_scraping(url, tags_to_extract, is_async=True)
