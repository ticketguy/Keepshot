"""Content scraper service - fetches and processes different content types"""
import os
import hashlib
import aiohttp
import httpx
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from PIL import Image
import yt_dlp

from app.config import settings
from app.core.logging import get_logger
from app.models.bookmark import ContentType

logger = get_logger(__name__)


class ContentScraper:
    """
    Content scraper for multiple content types.
    Handles URLs, images, videos, PDFs, and text.
    """

    def __init__(self):
        self.storage_path = Path(settings.storage_path)

    async def scrape(self, content_type: ContentType, url: Optional[str] = None, raw_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Main scraping method that routes to appropriate handler.

        Returns:
            {
                "content": str,  # Extracted text content
                "content_hash": str,  # SHA256 hash
                "file_path": Optional[str],  # Path to downloaded file
                "metadata": dict,  # Additional metadata
            }
        """
        try:
            if content_type == ContentType.URL:
                return await self._scrape_url(url)
            elif content_type == ContentType.IMAGE:
                return await self._download_image(url)
            elif content_type == ContentType.VIDEO:
                return await self._extract_video_metadata(url)
            elif content_type == ContentType.PDF:
                return await self._download_and_parse_pdf(url)
            elif content_type == ContentType.TEXT:
                return self._process_text(raw_content)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
        except Exception as e:
            logger.error("scrape_failed", content_type=content_type, url=url, error=str(e))
            raise

    async def _scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from a URL (tries Playwright first for JS-heavy sites, falls back to httpx)"""
        try:
            # Try simple HTTP request first (faster)
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                response.raise_for_status()

                # Check if it's HTML
                content_type = response.headers.get("content-type", "").lower()
                if "html" in content_type:
                    soup = BeautifulSoup(response.text, "lxml")

                    # Remove script and style tags
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Extract text
                    text = soup.get_text(separator="\n", strip=True)

                    # Extract metadata
                    title = soup.find("title")
                    title_text = title.string if title else None

                    metadata = {
                        "title": title_text,
                        "url": str(response.url),
                        "status_code": response.status_code,
                        "scraped_at": datetime.utcnow().isoformat(),
                    }

                    # Try to extract Open Graph metadata
                    og_title = soup.find("meta", property="og:title")
                    og_description = soup.find("meta", property="og:description")
                    if og_title:
                        metadata["og_title"] = og_title.get("content")
                    if og_description:
                        metadata["og_description"] = og_description.get("content")

                    content_hash = hashlib.sha256(text.encode()).hexdigest()

                    return {
                        "content": text,
                        "content_hash": content_hash,
                        "file_path": None,
                        "metadata": metadata,
                    }

        except Exception as e:
            logger.warning("simple_scrape_failed", url=url, error=str(e), msg="Falling back to Playwright")

        # Fallback to Playwright for JS-heavy sites
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=60000)

                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")

                # Remove script and style tags
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text(separator="\n", strip=True)

                # Get metadata
                title = await page.title()
                metadata = {
                    "title": title,
                    "url": page.url,
                    "scraped_at": datetime.utcnow().isoformat(),
                    "method": "playwright",
                }

                await browser.close()

                content_hash = hashlib.sha256(text.encode()).hexdigest()

                return {
                    "content": text,
                    "content_hash": content_hash,
                    "file_path": None,
                    "metadata": metadata,
                }

        except Exception as e:
            logger.error("playwright_scrape_failed", url=url, error=str(e))
            raise

    async def _download_image(self, url: str) -> Dict[str, Any]:
        """Download and process image"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    response.raise_for_status()
                    image_data = await response.read()

                    # Generate filename
                    filename = hashlib.sha256(image_data).hexdigest() + Path(url).suffix
                    file_path = self.storage_path / "images" / filename

                    # Ensure directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Save image
                    with open(file_path, "wb") as f:
                        f.write(image_data)

                    # Get image metadata
                    with Image.open(file_path) as img:
                        metadata = {
                            "width": img.width,
                            "height": img.height,
                            "format": img.format,
                            "mode": img.mode,
                            "size_bytes": len(image_data),
                            "url": url,
                        }

                    content_hash = hashlib.sha256(image_data).hexdigest()

                    return {
                        "content": f"Image: {url} ({img.width}x{img.height}, {img.format})",
                        "content_hash": content_hash,
                        "file_path": str(file_path),
                        "metadata": metadata,
                    }

        except Exception as e:
            logger.error("image_download_failed", url=url, error=str(e))
            raise

    async def _extract_video_metadata(self, url: str) -> Dict[str, Any]:
        """Extract video metadata (doesn't download video, just metadata)"""
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                metadata = {
                    "title": info.get("title"),
                    "description": info.get("description"),
                    "duration": info.get("duration"),
                    "uploader": info.get("uploader"),
                    "upload_date": info.get("upload_date"),
                    "view_count": info.get("view_count"),
                    "like_count": info.get("like_count"),
                    "url": url,
                }

                # Create content summary
                content = f"Video: {info.get('title')}\n"
                content += f"Uploader: {info.get('uploader')}\n"
                content += f"Description: {info.get('description', '')[:500]}\n"
                content += f"Duration: {info.get('duration')} seconds\n"
                content += f"Views: {info.get('view_count')}\n"

                content_hash = hashlib.sha256(content.encode()).hexdigest()

                return {
                    "content": content,
                    "content_hash": content_hash,
                    "file_path": None,
                    "metadata": metadata,
                }

        except Exception as e:
            logger.error("video_metadata_extraction_failed", url=url, error=str(e))
            raise

    async def _download_and_parse_pdf(self, url: str) -> Dict[str, Any]:
        """Download and extract text from PDF"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    response.raise_for_status()
                    pdf_data = await response.read()

                    # Check file size
                    if len(pdf_data) > settings.max_file_size * 1024 * 1024:
                        raise ValueError(f"PDF file too large: {len(pdf_data)} bytes")

                    # Generate filename
                    filename = hashlib.sha256(pdf_data).hexdigest() + ".pdf"
                    file_path = self.storage_path / "pdfs" / filename

                    # Ensure directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Save PDF
                    with open(file_path, "wb") as f:
                        f.write(pdf_data)

                    # Extract text
                    reader = PdfReader(file_path)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"

                    metadata = {
                        "num_pages": len(reader.pages),
                        "size_bytes": len(pdf_data),
                        "url": url,
                    }

                    # Try to get PDF metadata
                    if reader.metadata:
                        metadata.update({
                            "title": reader.metadata.get("/Title"),
                            "author": reader.metadata.get("/Author"),
                            "subject": reader.metadata.get("/Subject"),
                        })

                    content_hash = hashlib.sha256(text.encode()).hexdigest()

                    return {
                        "content": text,
                        "content_hash": content_hash,
                        "file_path": str(file_path),
                        "metadata": metadata,
                    }

        except Exception as e:
            logger.error("pdf_download_failed", url=url, error=str(e))
            raise

    def _process_text(self, text: str) -> Dict[str, Any]:
        """Process raw text content"""
        content_hash = hashlib.sha256(text.encode()).hexdigest()

        return {
            "content": text,
            "content_hash": content_hash,
            "file_path": None,
            "metadata": {
                "length": len(text),
                "word_count": len(text.split()),
            },
        }


# Global scraper instance
scraper = ContentScraper()
