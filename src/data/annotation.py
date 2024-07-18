from dotenv import load_dotenv
import os
import json
import time
import random
from pathlib import Path

# Third-party libraries
import openai
import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

# Utility
from tqdm import tqdm
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(filename='annotation_debug.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

RESPONSE_DIR = Path('data/raw')
PROCESSED_DIR = Path('data/processed')
ANNOTATED_DIR = Path('data/annotated')
MAX_TOKENS = 2000  # GPT-3.5-turbo setting no less than 1500 works

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
API_KEY = os.getenv("OPENAI_API_KEY")

# Environment Check
if API_KEY is None:     
    logging.error("OPENAI_API_KEY environment variable not set.")    
    raise SystemExit("OPENAI_API_KEY environment variable not set.")

# Initialize OpenAI and spaCy
openai.api_key = API_KEY
nlp = spacy.blank("en")

# Load fields and categories
with open('configs/fields.json', 'r') as f:
    FIELDS = json.load(f)

with open('configs/categories.json', 'r') as f:
    CATEGORIES = json.load(f)

def split_text(text: str, max_tokens: int = MAX_TOKENS) -> list[str]:
    doc = nlp(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for token in doc:
        token_length = len(token.text_with_ws)
        if current_length + token_length > max_tokens and current_chunk:
            chunks.append(''.join(current_chunk).strip())
            current_chunk = []
            current_length = 0
        
        current_chunk.append(token.text_with_ws)
        current_length += token_length

    if current_chunk:
        chunks.append(''.join(current_chunk).strip())

    return chunks

def create_prompt(text: str, field: str) -> str:
    return f"""Extract the '{field}' from the following text.
If multiple values are found, list each separately.
If no information is found, respond with 'Not found'.

Text:
{text}

Provide your response in the following format:
{field}: Extracted information
If multiple values are found, list each on a new line."""

def exponential_backoff(attempt: int, max_delay: int = 60) -> None:
    delay = min(max_delay, (2 ** attempt) + random.uniform(0, 1))
    time.sleep(delay)

def annotate_field(text: str, field: str) -> tuple[str, str]:
    chunks = split_text(text)
    all_annotations = []
    
    for chunk in chunks:
        prompt = create_prompt(chunk, field)
        max_attempts = 8
        for attempt in range(max_attempts):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts specific information from text."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=100
                )
                annotation = response['choices'][0]['message']['content'].strip()
                logging.debug(f"GPT-3 annotation for {field} (chunk):\n{annotation}")
                if annotation != "Not found":
                    all_annotations.append(annotation)
                break
            except openai.error.RateLimitError as e:
                logging.warning(f"Rate limit error on attempt {attempt + 1}: {e}")
                exponential_backoff(attempt)
            except openai.error.OpenAIError as e:
                logging.warning(f"OpenAI API error on attempt {attempt + 1}: {e}")
                exponential_backoff(attempt)
        else:
            logging.error(f"Failed to annotate field {field} after {max_attempts} attempts")
    
    return field, "\n".join(all_annotations) if all_annotations else "Not found"

def process_json_file(filepath: Path) -> tuple[dict, str]:
    with open(filepath, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    title = json_data.get('title', '')
    url = json_data.get('url', '')
    content = json_data.get('content', '')
    
    full_text = f"Title: {title}\nURL: {url}\nContent: {content}"
    
    annotations = {field: annotate_field(full_text, field)[1] for field in FIELDS}
    time.sleep(1)  # Small delay between field annotations
    
    return annotations, full_text

def create_spacy_doc(text: str, annotations: dict) -> spacy.tokens.Doc:
    doc = nlp(text)
    ents = []
    for field, annotation in annotations.items():
        if annotation != "Not found":
            for value in annotation.split('\n'):
                if ':' in value:
                    _, extracted = value.split(':', 1)
                    extracted = extracted.strip()
                    start = text.find(extracted)
                    if start != -1:
                        end = start + len(extracted)
                        span = doc.char_span(start, end, label=field)
                        if span is not None:
                            ents.append(span)
    
    doc.ents = filter_spans(ents)
    return doc

def save_spacy_doc(doc: spacy.tokens.Doc, output_path: Path) -> None:
    doc_bin = DocBin(docs=[doc])
    doc_bin.to_disk(output_path)

def annotate_data(raw_dir: Path, annotated_dir: Path) -> None:
    for filepath in tqdm(list(raw_dir.glob('*.json'))):
        try:
            logging.info(f"Processing file: {filepath}")
            annotations, full_text = process_json_file(filepath)
            
            doc = create_spacy_doc(full_text, annotations)
            
            output_path = annotated_dir / f"{filepath.stem}.spacy"
            save_spacy_doc(doc, output_path)
            
            filepath.rename(PROCESSED_DIR / filepath.name)
            
            time.sleep(5)  # Longer delay between files
        except Exception as e:
            logging.error(f"Error processing {filepath}: {str(e)}", exc_info=True)

if __name__ == "__main__":
    annotate_data(RESPONSE_DIR, ANNOTATED_DIR)