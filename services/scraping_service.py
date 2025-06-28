import asyncio
from typing import List

from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from bs4 import BeautifulSoup



def get_default_tags() -> List[str]:
    """Get default HTML tags for web scraping"""
    return ["p", "li", "div", "a", "span", "h1", "h2", "h3", "h4", "h5", "h6"]


class WebScrapingTool():

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
                
            html = html_docs[0].page_content if html_docs else ""
            clean_docs = []
            for d in html_docs:
                soup = BeautifulSoup(d.page_content, "html.parser")
                # remove attrs you don’t want
                for tag in soup.find_all(True):
                    for attr in ("style", "class", "id"):
                        tag.attrs.pop(attr, None)
                # drop empty tags
                for t in soup.find_all(True):
                    if not t.text.strip() and not t.find(True):
                        t.decompose()
                clean_docs.append(d.copy(update={"page_content": str(soup)}))
            
            bs4_t = BeautifulSoupTransformer()

            docs_transformed = bs4_t.transform_documents(
                clean_docs,                              
                unwanted_tags=("script", "style",        
                            "option", "i", "img"),
                tags_to_extract=tags_to_extract,           
                remove_comments=True                    
            )

            text_only = docs_transformed[0].page_content 
            print(len(text_only))
            with open("text_only.txt", "w", encoding="utf-8") as file:
                file.write(str(text_only))
                
            return f"""
                **Website Scraped:** {url}
                **Content Extracted:**

                {text_only}

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
