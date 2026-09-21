"""
Scraping and extraction engine using Trafilatura with BeautifulSoup4 + Markdownify fallback.
Handles async HTTP concurrency, polite rate limiting, and exponential retries.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
import trafilatura
from bs4 import BeautifulSoup
from markdownify import markdownify as md

logger = logging.getLogger("synclm.scraper")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SyncLM-Studio/1.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class ScrapeResult:
    def __init__(
        self,
        url: str,
        success: bool,
        content: str = "",
        title: Optional[str] = None,
        extractor: str = "none",
        word_count: int = 0,
        error: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        self.url = url
        self.success = success
        self.content = content
        self.title = title
        self.extractor = extractor
        self.word_count = word_count
        self.error = error
        self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "success": self.success,
            "title": self.title,
            "extractor": self.extractor,
            "word_count": self.word_count,
            "error": self.error,
            "status_code": self.status_code
        }


class DocScraper:
    def __init__(
        self,
        timeout_seconds: float = 25.0,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        concurrency: int = 4
    ):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.semaphore = asyncio.Semaphore(concurrency)

    async def fetch_html(self, client: httpx.AsyncClient, url: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """Fetch HTML content with retries and exponential backoff."""
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.get(
                    url,
                    headers=DEFAULT_HEADERS,
                    follow_redirects=True,
                    timeout=self.timeout_seconds
                )
                if response.status_code == 200:
                    return response.text, response.status_code, None
                elif response.status_code in (429, 500, 502, 503, 504):
                    if attempt < self.max_retries:
                        sleep_time = self.backoff_factor ** attempt
                        logger.warning(f"Got {response.status_code} for {url}, retrying in {sleep_time:.1f}s (attempt {attempt}/{self.max_retries})")
                        await asyncio.sleep(sleep_time)
                        continue
                return None, response.status_code, f"HTTP Error {response.status_code}"
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor ** attempt
                    await asyncio.sleep(sleep_time)
                    continue
                return None, None, f"Network Exception: {str(exc)}"
        return None, None, "Max retries exceeded"

    def extract_with_trafilatura(self, html: str, url: str) -> Optional[str]:
        """Extract clean body text and markdown using trafilatura."""
        try:
            extracted = trafilatura.extract(
                html,
                url=url,
                output_format="markdown",
                include_links=True,
                include_images=False,
                include_tables=True,
                favor_recall=True,
                no_fallback=False
            )
            return extracted
        except Exception as exc:
            logger.debug(f"Trafilatura extraction error for {url}: {exc}")
            return None

    def extract_with_bs4_markdownify(self, html: str, url: str) -> tuple[str, Optional[str]]:
        """
        Fallback extraction using BeautifulSoup4 cleaning and markdownify.
        Ideal for techdocs with specific article tags or JS portal remnants.
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title
        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        h1 = soup.find("h1")
        if h1 and h1.text:
            title = h1.text.strip()

        # Remove junk elements: scripts, navbars, footers, sidebars, cookie notices
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
            tag.decompose()

        for class_or_id in [
            "cookie", "banner", "sidebar", "nav", "menu", "header", "footer", 
            "breadcrumb", "toc", "feedback", "social-share"
        ]:
            for tag in soup.find_all(attrs={"class": lambda c: c and class_or_id in str(c).lower()}):
                tag.decompose()
            for tag in soup.find_all(attrs={"id": lambda i: i and class_or_id in str(i).lower()}):
                tag.decompose()

        # Target main content container if present
        main_content = (
            soup.find("main") or
            soup.find("article") or
            soup.find(attrs={"role": "main"}) or
            soup.find(class_=lambda c: c and any(k in str(c).lower() for k in ["doc-content", "article-body", "page-content", "content"])) or
            soup.body or
            soup
        )

        html_str = str(main_content)
        markdown_text = md(
            html_str,
            heading_style="ATX",
            strip=["script", "style"],
            bullets="-",
            autolinks=True
        )
        return markdown_text.strip(), title

    async def scrape(self, client: httpx.AsyncClient, url: str, fallback_title: Optional[str] = None) -> ScrapeResult:
        """Scrapes a single documentation URL with trafilatura and fallback."""
        async with self.semaphore:
            html, status_code, err = await self.fetch_html(client, url)
            if not html:
                return ScrapeResult(
                    url=url,
                    success=False,
                    error=err or "No HTML returned",
                    status_code=status_code
                )

            # 1. Primary: Trafilatura
            content = self.extract_with_trafilatura(html, url)
            extractor_used = "trafilatura"

            # Check if extraction succeeded with adequate substance (> 80 words)
            if not content or len(content.split()) < 80:
                logger.info(f"Trafilatura yielded insufficient content ({len(content.split()) if content else 0} words) for {url}, falling back to BS4 + markdownify.")
                content, bs4_title = self.extract_with_bs4_markdownify(html, url)
                extractor_used = "bs4_markdownify"
                doc_title = bs4_title or fallback_title or "Documentation Article"
            else:
                # Try to get title from metadata or fallback
                metadata = trafilatura.extract_metadata(html)
                doc_title = (metadata.title if metadata and metadata.title else None) or fallback_title or "Documentation Article"

            word_count = len(content.split()) if content else 0
            if word_count < 20:
                return ScrapeResult(
                    url=url,
                    success=False,
                    error="Extracted content too brief or empty after boiler-plate stripping",
                    status_code=status_code,
                    extractor=extractor_used,
                    word_count=word_count
                )

            return ScrapeResult(
                url=url,
                success=True,
                content=content,
                title=doc_title,
                extractor=extractor_used,
                word_count=word_count,
                status_code=status_code
            )
