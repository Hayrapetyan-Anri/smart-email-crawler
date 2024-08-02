import re
import time
import random
import asyncio
import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import logging
import concurrent.futures

# Define the CSE ID and API Key
CSE_ID = ''
API_KEY = ''

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

async def fetch(session, url):
    try:
        async with session.get(url, timeout=ClientTimeout(total=10)) as response:
            if response.status == 200:
                return await response.text()
            else:
                logger.warning(f"Failed to fetch {url} with status code {response.status}")
                return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout while fetching {url}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch {url} with aiohttp: {e}")
        return None

async def fetch_with_selenium(url):
    def fetch_page():
        try:
            driver.set_page_load_timeout(10)
            driver.get(url)
            return driver.page_source
        except Exception as e:
            return None

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = loop.run_in_executor(executor, fetch_page)
        try:
            return await asyncio.wait_for(future, timeout=10)  # 15-second timeout
        except asyncio.TimeoutError:
            logger.error(f"Timeout while fetching {url} with Selenium")
            return None


async def process_url(session, url, keyword, email_pattern, name_email_pattern, emails):
    try:
        if 'http' not in url:
            url = 'http://' + url

        logger.info(f"Fetching {url}")
        
        # Try fetching with aiohttp first
        page_text = await fetch(session, url)
        
        # If aiohttp fails, fallback to Selenium
        if page_text is None:
            page_text = await fetch_with_selenium(url)
        
        if page_text and keyword in page_text and "@" in page_text:
            soup = BeautifulSoup(page_text, 'html.parser')
            found_emails = email_pattern.findall(soup.get_text())
            for email in found_emails:
                if name_email_pattern.match(email) and not any(x in email for x in ['info', 'contact']):
                    emails.add(email)
    except Exception as e:
        logger.error(f"Failed to retrieve {url}: {e}")

async def search_emails(keyword):
    base_search_url = "https://www.googleapis.com/customsearch/v1"
    
    emails = set()
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    name_email_pattern = re.compile(r'[a-zA-Z]+\.[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    page = 1  # Start index for the first page
    connector = TCPConnector(limit_per_host=10)

    async with ClientSession(connector=connector) as session:
        while page <= 91:  # Ensure the start parameter does not exceed 91
            params = {
                'key': API_KEY,
                'cx': CSE_ID,
                'q': f'intext:"{keyword}" intext:"@"',  # Exact match for keyword and include @
                'start': page,
            }
            
            try:
                async with session.get(base_search_url, params=params) as response:
                    if response.status != 200:
                        logger.warning("LIMIT EXCEEDED")
                        break
                    results = await response.json()
                    
                    if 'items' not in results:
                        break
                    
                    tasks = []
                    for item in results['items']:
                        link = item['link']
                        tasks.append(process_url(session, link, keyword, email_pattern, name_email_pattern, emails))
                    
                    await asyncio.gather(*tasks)
                
                # Sleep to prevent being blocked and randomize the delay
                await asyncio.sleep(random.uniform(2, 5))
                
                page += 10  # Increment by 10 for the next set of results
            except Exception as e:
                logger.error(f"Failed to retrieve search results: {e}")
                break
    
    return emails

if __name__ == "__main__":
    keyword = "emails"
    emails = asyncio.run(search_emails(keyword))
    for email in emails:
        logger.info(f"Found email: {email}")

    driver.quit()
