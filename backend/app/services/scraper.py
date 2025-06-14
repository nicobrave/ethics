from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import re

from app.config import settings

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.timeout = settings.SCRAPING_TIMEOUT * 1000  # Convert to ms
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    async def scrape_website(self, url: str, deep_scan: bool = False) -> Dict:
        """Scrape website content"""
        try:
            page = await self.browser.new_page()
            await page.set_extra_http_headers({
                'User-Agent': settings.USER_AGENT
            })
            
            # Navigate to main page
            logger.info(f"Scraping {url}")
            await page.goto(url, timeout=self.timeout, wait_until='networkidle')
            
            # Get main content
            content = await page.content()
            title = await page.title()
            
            # Extract text content
            soup = BeautifulSoup(content, 'html.parser')
            text_content = self._extract_text_content(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            result = {
                'url': url,
                'title': title,
                'content': text_content,
                'metadata': metadata,
                'pages_analyzed': 1,
                'content_length': len(text_content)
            }
            
            # Deep scan - get additional pages
            if deep_scan:
                additional_content = await self._deep_scan(page, url)
                result.update(additional_content)
            
            await page.close()
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            raise Exception(f"Failed to scrape website: {str(e)}")

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:50000]  # Limit content length

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                metadata[name] = content
        
        # Links to important pages
        important_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().lower().strip()
            
            if any(keyword in href or keyword in text for keyword in 
                   ['privacy', 'terms', 'about', 'contact', 'policy']):
                important_links.append({
                    'text': text,
                    'href': link['href']
                })
        
        metadata['important_links'] = important_links
        return metadata

    async def _deep_scan(self, page: Page, base_url: str) -> Dict:
        """Perform deep scan of additional pages"""
        additional_content = {}
        pages_scanned = 1
        
        # Look for privacy policy and terms of service
        important_pages = ['privacy', 'terms', 'about']
        
        for page_type in important_pages:
            try:
                # Try to find and scrape the page
                page_content = await self._scrape_specific_page(page, base_url, page_type)
                if page_content:
                    additional_content[f'{page_type}_content'] = page_content
                    pages_scanned += 1
            except Exception as e:
                logger.warning(f"Could not scrape {page_type} page: {str(e)}")
        
        return {
            'additional_content': additional_content,
            'pages_analyzed': pages_scanned,
            'deep_scan_completed': True
        }

    async def _scrape_specific_page(self, page: Page, base_url: str, page_type: str) -> Optional[str]:
        """Scrape specific page type"""
        # Common URL patterns for different page types
        patterns = {
            'privacy': ['/privacy', '/privacy-policy', '/privacidad'],
            'terms': ['/terms', '/terms-of-service', '/terminos'],
            'about': ['/about', '/about-us', '/acerca']
        }
        
        for pattern in patterns.get(page_type, []):
            try:
                url = urljoin(base_url, pattern)
                await page.goto(url, timeout=10000)
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                return self._extract_text_content(soup)[:10000]  # Limit content
            except:
                continue
        
        return None 