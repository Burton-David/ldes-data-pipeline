import logging
import argparse
from tqdm import tqdm
import yaml
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.data.ingestion import ingest_data
from src.pipeline.ner_pipeline import LDESExtractionPipeline
from src.pipeline.rule_based_extraction import apply_rules, extract_technologies
from src.pipeline.data_cleaning import clean_data
from src.pipeline.data_validation import validate_data
from src.database.db_operations import DatabaseOperations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def process_energy_document(regulatory_document, ldes_extraction_pipeline, config):
    """
    Process individual energy storage documents (regulatory filings, press releases, etc.)
    
    Handles the complexity of LDES data where a single project announcement might
    contain capacity specs, timeline info, and technology details mixed with
    regulatory language and financial information.
    """
    try:
        # Clean energy storage document text (handles PDF extraction artifacts)
        cleaned_energy_data = clean_data(regulatory_document)
        
        # Extract LDES project specifications using domain-trained models
        extracted_project_specs = ldes_extraction_pipeline.extract_project_specs(
            cleaned_energy_data['text'], 
            cleaned_energy_data.get('sector', 'ldes')
        )
        
        # Apply energy storage rule-based patterns (capacity calculations, unit normalization)
        regulatory_pattern_extracts = apply_rules(cleaned_energy_data['text'])
        
        # Identify and categorize energy storage technologies 
        identified_ldes_technologies = extract_technologies(cleaned_energy_data['text'])
        
        # Merge all energy project data sources
        comprehensive_project_data = {
            **extracted_project_specs, 
            **regulatory_pattern_extracts, 
            'Technology': ', '.join(identified_ldes_technologies)
        }
        
        # Validate energy storage data consistency (capacity units, timeline logic, etc.)
        validated_project_specs, data_quality_issues = validate_data(comprehensive_project_data)
        
        if data_quality_issues:
            logger.warning(
                f"Energy data quality issues for document {regulatory_document.get('uid', 'unknown')}: "
                f"{data_quality_issues}"
            )
        
        logger.info(f"Successfully processed LDES document: {regulatory_document.get('uid', 'unknown')}")
        logger.debug(f"Extracted project specifications: {validated_project_specs}")
        
        return validated_project_specs
        
    except Exception as processing_error:
        logger.error(
            f"Error processing energy storage document {regulatory_document.get('uid', 'unknown')}: "
            f"{str(processing_error)}"
        )
        return None

def main(config_path):
    """
    Main LDES data intelligence pipeline.
    
    Designed for processing large volumes of energy storage regulatory filings,
    press releases, and industry reports to extract structured market intelligence.
    """
    try:
        pipeline_config = load_config(config_path)
        
        # Initialize energy storage database connection
        energy_storage_db = DatabaseOperations(
            host=pipeline_config['database']['host'],
            port=pipeline_config['database']['port'],
            dbname=pipeline_config['database']['name'],
            user=pipeline_config['database']['user'],
            password=pipeline_config['database']['password']
        )
        
        # Ingest raw energy storage documents (PDFs, URLs, press releases)
        raw_energy_documents = ingest_data(pipeline_config['data']['raw_dir'])
        
        # Initialize LDES-specialized extraction pipeline
        ldes_extraction_pipeline = LDESExtractionPipeline(
            ldes_model_path=pipeline_config['models']['spacy_ner_dir'],
            openai_api_key=pipeline_config['openai']['api_key'],
            project_fields_path=os.path.join('configs', 'fields.json'),
            energy_categories_path=os.path.join('configs', 'categories.json'),
            openai_model=pipeline_config['openai']['model']
        )
        
        # Process energy storage documents concurrently
        # Regulatory PDFs are large and slow, so parallel processing is essential
        max_concurrent_workers = pipeline_config.get('max_workers', 4)
        
        with ThreadPoolExecutor(max_workers=max_concurrent_workers) as executor:
            document_processing_futures = {
                executor.submit(process_energy_document, doc, ldes_extraction_pipeline, pipeline_config): doc 
                for doc in raw_energy_documents
            }
            
            processed_count = 0
            for completed_future in tqdm(
                as_completed(document_processing_futures), 
                total=len(raw_energy_documents), 
                desc="Processing LDES documents"
            ):
                source_document = document_processing_futures[completed_future]
                try:
                    extracted_project_data = completed_future.result()
                    if extracted_project_data:
                        energy_storage_db.insert_project(extracted_project_data)
                        processed_count += 1
                except Exception as processing_error:
                    logger.error(
                        f"Failed to process energy document {source_document.get('uid', 'unknown')}: "
                        f"{str(processing_error)}"
                    )
        
        energy_storage_db.close()
        logger.info(
            f"LDES data processing complete. Successfully processed {processed_count} energy storage documents. "
            f"Project data saved to database for market analysis."
        )
    
    except Exception as pipeline_error:
        logger.error(f"LDES pipeline execution failed: {str(pipeline_error)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the LDES market intelligence data pipeline. "
                   "Processes energy storage regulatory filings, press releases, and industry reports "
                   "to extract structured project data for market analysis."
    )
    parser.add_argument(
        "--config", 
        default="configs/config.yaml", 
        help="Path to LDES pipeline configuration file"
    )
    args = parser.parse_args()
    
    main(args.config)
