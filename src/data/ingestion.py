import os
import logging
import json
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
import PyPDF2
import io
from pathlib import Path
from tqdm import tqdm
import time
import random
import hashlib
import yaml

# Configure logging
logging.basicConfig(filename='logs/scraping_log.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create directories to store the JSON responses
RESPONSE_DIR = Path(config['data']['raw_dir'])
RESPONSE_DIR.mkdir(parents=True, exist_ok=True)

def generate_uid(row):
    """Generate a unique identifier for a row."""
    return hashlib.md5(str(row).encode()).hexdigest()

async def fetch_url(session, url, max_attempts=5):
    """Fetch URL content with retries and backoff."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for attempt in range(max_attempts):
        try:
            async with session.get(url, headers=headers, timeout=30) as response:
                response.raise_for_status()
                return await response.read(), response.headers.get('Content-Type', '')
        except aiohttp.ClientError as e:
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
            else:
                logging.error(f"Failed to fetch {url} after {max_attempts} attempts")
                return None, None

def extract_text_from_html(html_content):
    """Extract text content from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator='\n', strip=True)
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def extract_text_from_pdf(pdf_content):
    """Extract text content from PDF."""
    pdf_file = io.BytesIO(pdf_content)
    reader = PyPDF2.PdfReader(pdf_file)
    return '\n'.join(page.extract_text() for page in reader.pages)

async def process_url(session, url, uid):
    """Process a single URL."""
    try:
        content, content_type = await fetch_url(session, url)
        if not content:
            return None

        if 'application/pdf' in content_type:
            text = extract_text_from_pdf(content)
        elif 'text/html' in content_type:
            text = extract_text_from_html(content)
        else:
            logging.warning(f"Unsupported content type for {url}: {content_type}")
            return None
        
        title = BeautifulSoup(content, 'html.parser').title.string if 'text/html' in content_type else ''
        
        data = {
            "uid": uid,
            "url": url,
            "title": title,
            "content": text
        }
        
        filename = f"{uid}_{urlparse(url).netloc}_{urlparse(url).path.replace('/', '_')}.json"
        filepath = RESPONSE_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Successfully processed and saved: {url}")
        return filepath
    
    except Exception as e:
        logging.error(f"Error processing {url}: {str(e)}")
        return None

async def process_urls(urls):
    """Process multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [process_url(session, url, uid) for url, uid in urls]
        return await asyncio.gather(*tasks)

def ingest_data(csv_path):
    """Main function to process all URLs from the CSV file."""
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['uid'] = df.apply(generate_uid, axis=1)
    
    url_columns = config['ingestion']['url_columns']
    
    all_urls = []
    for column in url_columns:
        all_urls.extend([(row[column], row['uid']) for _, row in df.iterrows() if pd.notna(row[column])])
    
    chunk_size = config['ingestion']['chunk_size']
    results = []
    
    for i in tqdm(range(0, len(all_urls), chunk_size), desc="Processing URL chunks"):
        chunk = all_urls[i:i+chunk_size]
        chunk_results = asyncio.run(process_urls(chunk))
        results.extend([r for r in chunk_results if r])
        time.sleep(config['ingestion']['chunk_delay'])
    
    for result in results:
        print(f"Processed and saved: {result}")

if __name__ == "__main__":
    csv_path = config['data']['sources_csv']
    ingest_data(csv_path)