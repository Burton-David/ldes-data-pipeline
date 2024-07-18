import logging
import argparse
from tqdm import tqdm
import yaml
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.data.ingestion import ingest_data
from src.pipeline.ner_pipeline import NERPipeline
from src.pipeline.rule_based_extraction import apply_rules, extract_technologies
from src.pipeline.data_cleaning import clean_data
from src.pipeline.data_validation import validate_data
from src.database.db_operations import DatabaseOperations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def process_document(document, ner_pipeline, config):
    try:
        # Clean data
        cleaned_data = clean_data(document)
        
        # Extract entities using NER
        ner_entities = ner_pipeline.extract_entities(cleaned_data['text'], cleaned_data.get('sector', 'ldes'))
        
        # Apply rule-based extraction
        rule_based_entities = apply_rules(cleaned_data['text'])
        
        # Extract technologies
        technologies = extract_technologies(cleaned_data['text'])
        
        # Merge all extracted entities
        merged_entities = {**ner_entities, **rule_based_entities, 'Technology': ', '.join(technologies)}
        
        # Validate entities
        validated_entities, errors = validate_data(merged_entities)
        
        if errors:
            logger.warning(f"Validation errors for document {document.get('uid', 'unknown')}: {errors}")
        
        logger.info(f"Processed document: {document.get('uid', 'unknown')}")
        logger.debug(f"Extracted and validated entities: {validated_entities}")
        
        return validated_entities
    except Exception as e:
        logger.error(f"Error processing document {document.get('uid', 'unknown')}: {str(e)}")
        return None

def main(config_path):
    try:
        config = load_config(config_path)
        
        # Initialize database connection
        db = DatabaseOperations(
            host=config['database']['host'],
            port=config['database']['port'],
            dbname=config['database']['name'],
            user=config['database']['user'],
            password=config['database']['password']
        )
        
        # Ingest data
        raw_data = ingest_data(config['data']['raw_dir'])
        
        # Initialize NER pipeline
        ner_pipeline = NERPipeline(
            config['models']['spacy_ner_dir'],
            config['openai']['api_key'],
            os.path.join('configs', 'fields.json'),
            os.path.join('configs', 'categories.json'),
            config['openai']['model']
        )
        
        # Process documents in parallel
        with ThreadPoolExecutor(max_workers=config.get('max_workers', 4)) as executor:
            future_to_doc = {executor.submit(process_document, doc, ner_pipeline, config): doc for doc in raw_data}
            for future in tqdm(as_completed(future_to_doc), total=len(raw_data), desc="Processing documents"):
                doc = future_to_doc[future]
                try:
                    result = future.result()
                    if result:
                        db.insert_project(result)
                except Exception as e:
                    logger.error(f"Error processing document {doc.get('uid', 'unknown')}: {str(e)}")
        
        db.close()
        logger.info("Processing complete. All data saved to database.")
    
    except Exception as e:
        logger.error(f"An error occurred during execution: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the LDES data processing pipeline.")
    parser.add_argument("--config", default="config.yaml", help="Path to the configuration file")
    args = parser.parse_args()
    
    main(args.config)