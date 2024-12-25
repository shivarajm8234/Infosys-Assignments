import aiohttp
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import logging
import asyncio
import random

logger = logging.getLogger(__name__)

class WebScrapingBot:
    def __init__(self):
        """Initialize the web scraping bot."""
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
    async def init_session(self):
        """Initialize aiohttp session with retry options."""
        try:
            if self.session is None or self.session.closed:
                connector = aiohttp.TCPConnector(
                    limit=10,
                    force_close=False,
                    enable_cleanup_closed=True,
                    verify_ssl=False  # Only if needed for testing
                )
                self.session = aiohttp.ClientSession(
                    headers=self.headers,
                    connector=connector,
                    timeout=self.timeout
                )
                logger.debug("Created new aiohttp session with custom connector")
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise
        
    async def scrape_webpage(self, url: str, max_retries: int = 3) -> str:
        """Fetch webpage content with retries and advanced error handling."""
        retries = 0
        last_exception = None
        
        while retries < max_retries:
            try:
                if self.session is None or self.session.closed:
                    await self.init_session()
                    if self.session is None:
                        raise Exception("Failed to initialize session")
                
                # Add random delay between retries to avoid rate limiting
                if retries > 0:
                    delay = 2 ** retries + random.uniform(0, 1)
                    logger.info(f"Waiting {delay:.2f} seconds before retry {retries + 1}")
                    await asyncio.sleep(delay)
                
                logger.info(f"Attempting to scrape URL: {url} (Attempt {retries + 1}/{max_retries})")
                async with self.session.get(url, allow_redirects=True, ssl=False, compress=True) as response:
                    status = response.status
                    logger.info(f"Request to {url} returned status: {status}")
                    
                    # Handle different status codes
                    if status == 200:
                        content = await response.text(encoding='utf-8', errors='replace')
                        if content.strip():  # Verify we got actual content
                            logger.info(f"Successfully scraped content from {url}")
                            return content
                        else:
                            raise Exception("Received empty response from server")
                    elif status == 500:
                        logger.error(f"Server error (500) on attempt {retries + 1}/{max_retries}")
                        if retries == max_retries - 1:
                            raise aiohttp.ClientError(f"Persistent server error (500) after {max_retries} attempts")
                    elif status in [403, 429]:
                        logger.error(f"Rate limited or blocked (status {status})")
                        # Longer delay for rate limiting
                        await asyncio.sleep(10 + (5 * retries))
                    elif status >= 400:
                        error_msg = f"HTTP {status} error occurred"
                        if status in [404, 401, 403]:  # Don't retry client errors
                            raise aiohttp.ClientError(f"Client error: {status} - {error_msg}")
                        logger.error(error_msg)
                    
                    response.raise_for_status()
                    
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error on attempt {retries + 1}/{max_retries}: {str(e)}")
                last_exception = e
            except asyncio.TimeoutError:
                logger.error(f"Request timed out on attempt {retries + 1}/{max_retries}")
                last_exception = Exception("Request timed out")
            except Exception as e:
                logger.error(f"Unexpected error on attempt {retries + 1}/{max_retries}: {str(e)}")
                last_exception = e
            finally:
                retries += 1
                
                # Close session on final retry if we have an error
                if retries == max_retries and last_exception is not None:
                    try:
                        await self.close_session()
                    except Exception as e:
                        logger.error(f"Error closing session: {str(e)}")
        
        # If we've exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception
        else:
            raise Exception("Failed to scrape webpage after all retries")

    def _extract_main_content(self, html_content: str) -> Dict[str, Any]:
        """Extract main content from HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'iframe', 'noscript']):
                element.decompose()
            
            # Extract title
            title = ''
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.string.strip() if title_tag.string else ''
            
            # Extract meta description
            meta_description = ''
            meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_desc_tag:
                meta_description = meta_desc_tag.get('content', '').strip()
            
            # Extract headings
            headings = {}
            for i in range(1, 7):
                h_tags = soup.find_all(f'h{i}')
                if h_tags:
                    headings[str(i)] = [h.get_text().strip() for h in h_tags if h.get_text().strip()]
            
            # Extract paragraphs
            paragraphs = []
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if text and len(text) > 20:  # Filter out short paragraphs
                    paragraphs.append(text)
            
            # Extract links
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text().strip()
                if href and text and not href.startswith('#'):
                    links.append({
                        'url': href,
                        'text': text
                    })
            
            # Extract lists
            lists = {
                'ordered': [],
                'unordered': []
            }
            
            # Ordered lists
            for ol in soup.find_all('ol'):
                items = [li.get_text().strip() for li in ol.find_all('li') if li.get_text().strip()]
                if items:
                    lists['ordered'].append(items)
            
            # Unordered lists
            for ul in soup.find_all('ul'):
                items = [li.get_text().strip() for li in ul.find_all('li') if li.get_text().strip()]
                if items:
                    lists['unordered'].append(items)
            
            # Extract tables
            tables = []
            for table in soup.find_all('table'):
                table_data = []
                rows = table.find_all('tr')
                
                # Get headers
                headers = []
                header_row = table.find('thead')
                if header_row:
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                
                # Get rows
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    if cols:
                        row_data = [col.get_text().strip() for col in cols]
                        table_data.append(row_data)
                
                if table_data:
                    tables.append({
                        'headers': headers,
                        'data': table_data
                    })
            
            # Extract contact information
            contact_info = {
                'emails': [],
                'phones': [],
                'addresses': []
            }
            
            # Email pattern
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, str(soup))
            contact_info['emails'] = list(set(emails))
            
            # Phone pattern (basic)
            phone_pattern = r'\+?[\d\s-]{10,}'
            phones = re.findall(phone_pattern, str(soup))
            contact_info['phones'] = [p.strip() for p in phones if len(re.sub(r'\D', '', p)) >= 10]
            
            # Extract social media links
            social_patterns = {
                'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
                'youtube.com', 'github.com', 'pinterest.com'
            }
            social_links = []
            for a in soup.find_all('a', href=True):
                href = a['href'].lower()
                if any(pattern in href for pattern in social_patterns):
                    social_links.append(href)
            
            return {
                'title': title,
                'meta_description': meta_description,
                'headings': headings,
                'paragraphs': paragraphs,
                'links': links,
                'lists': lists,
                'tables': tables,
                'contact_info': contact_info,
                'social_links': list(set(social_links))
            }
            
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return {
                'title': '',
                'meta_description': '',
                'headings': {},
                'paragraphs': [],
                'links': [],
                'lists': {'ordered': [], 'unordered': []},
                'tables': [],
                'contact_info': {'emails': [], 'phones': [], 'addresses': []},
                'social_links': []
            }

    async def close_session(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.debug("Closed aiohttp session")
