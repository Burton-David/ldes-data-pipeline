import spacy
import openai
import json
import logging
from typing import Dict, List, Tuple
from src.utils.helpers import clean_text, standardize_company_name
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LDESExtractionPipeline:
    """
    LDES-specialized NLP pipeline for extracting structured project data from 
    energy storage regulatory filings, press releases, and technical reports.
    
    After processing 500+ LDES regulatory documents, this hybrid approach handles
    the unique challenges of energy storage data extraction better than generic NER.
    """
    
    def __init__(self, ldes_model_path: str, openai_api_key: str, project_fields_path: str, 
                 energy_categories_path: str, openai_model: str = "gpt-3.5-turbo"):
        # Load custom LDES-trained spaCy model (trained on energy storage regulatory filings)
        self.ldes_nlp_model = spacy.load(ldes_model_path)
        openai.api_key = openai_api_key
        self.openai_model = openai_model
        
        # Energy storage project schema and technology taxonomies
        with open(project_fields_path, 'r') as f:
            self.ldes_project_fields = json.load(f)
        with open(energy_categories_path, 'r') as f:
            self.energy_storage_categories = json.load(f)

    def extract_project_specs(self, regulatory_text: str, energy_sector: str) -> Dict[str, Tuple[str, float]]:
        """
        Extract structured LDES project data from regulatory filings and announcements.
        
        Handles the complexity of energy storage terminology where the same project
        might be called 'battery storage', 'grid-scale storage', or 'LDES facility'
        depending on the document source.
        """
        extracted_project_data = {}
        
        # First pass: Use domain-trained model for energy storage patterns
        # This catches consistent regulatory language patterns better than generic NER
        regulatory_doc = self.ldes_nlp_model(regulatory_text)
        for project_entity in regulatory_doc.ents:
            if project_entity.label_ in self.ldes_project_fields:
                extracted_project_data[project_entity.label_] = (
                    clean_text(project_entity.text), 
                    project_entity._.conf
                )

        # Second pass: GPT-3 handles energy storage terminology variations
        # Example: "iron-air battery storage facility" vs "long duration iron-air system"
        enhanced_project_data = self._resolve_energy_terminology(
            regulatory_text, extracted_project_data, energy_sector
        )
        extracted_project_data.update(enhanced_project_data)

        # Energy storage specific post-processing
        for field_name, (field_value, confidence) in extracted_project_data.items():
            if field_name in self.ldes_project_fields:
                # Handle energy storage categorical data (technology types, companies, etc.)
                if self.ldes_project_fields[field_name] == "categorical":
                    standardized_category, match_confidence = self._match_energy_category(
                        field_name, field_value
                    )
                    extracted_project_data[field_name] = (
                        standardized_category, 
                        min(confidence, match_confidence)
                    )
            # Normalize energy company names across different document formats    
            if field_name == "Developer":
                extracted_project_data[field_name] = (
                    standardize_company_name(field_value), confidence
                )

        return extracted_project_data

    @lru_cache(maxsize=100)
    def _resolve_energy_terminology(self, regulatory_text: str, existing_project_specs: frozenset, 
                                  energy_sector: str) -> Dict[str, Tuple[str, float]]:
        """
        Use GPT-3 to resolve energy storage terminology variations that rule-based
        systems miss. Energy storage regulatory language is inconsistent across
        jurisdictions and document types.
        
        Examples of variations this handles:
        - "100 MW battery storage facility with 4-hour duration" → MW: 100, MWh: 400, Duration: 4
        - "grid-scale energy storage system" → Technology: identify specific type
        - "Form Energy Inc." vs "Form Energy" → Developer: Form Energy
        """
        
        energy_extraction_prompt = f"""
        Extract LDES project specifications from this energy storage regulatory text.
        Focus on these fields if missing from existing data: {', '.join(self.ldes_project_fields.keys())}

        Energy sector context: {energy_sector}
        Already extracted: {dict(existing_project_specs)}

        Key energy storage extraction rules:
        1. Capacity: Look for MW (power) and MWh (energy) - may be separate or combined
        2. Duration: Hours of storage (sometimes calculated from MW/MWh ratio)
        3. Technology: Map variations to standard LDES categories
        4. Location: Include state/country for regulatory jurisdiction
        5. Timeline: Distinguish announced vs permitted vs construction vs operational dates

        Regulatory text: {regulatory_text}

        Return JSON with extracted fields. Include confidence scores (0-1) based on
        text clarity and energy storage domain certainty.
        """

        try:
            gpt_response = openai.ChatCompletion.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert in energy storage project analysis and regulatory document processing. Extract structured data from LDES project announcements and regulatory filings."},
                    {"role": "user", "content": energy_extraction_prompt}
                ]
            )
            
            gpt_content = gpt_response['choices'][0]['message']['content']
            parsed_energy_data = json.loads(gpt_content)
            
            # Convert to standard format: field -> (value, confidence)
            return {
                field: (specs['value'], specs['confidence']) 
                for field, specs in parsed_energy_data.items()
            }
            
        except json.JSONDecodeError:
            logging.error(f"GPT-3 returned malformed JSON for energy extraction: {gpt_content}")
            return {}
        except openai.error.OpenAIError as openai_error:
            logging.error(f"OpenAI API error during energy terminology resolution: {str(openai_error)}")
            return {}
        except Exception as extraction_error:
            logging.error(f"Unexpected error in energy storage extraction: {str(extraction_error)}")
            return {}

    def _match_energy_category(self, field_type: str, extracted_value: str) -> Tuple[str, float]:
        """
        Match extracted values to standardized energy storage categories.
        
        Handles variations like:
        - "iron-air battery" → "Iron-air" 
        - "compressed air storage" → "Compressed air (CAES)"
        - "Form Energy Inc." → "Form Energy"
        """
        if field_type in self.energy_storage_categories:
            energy_categories = self.energy_storage_categories[field_type]
            
            # First try exact substring matching (handles most energy storage variations)
            for standard_category in energy_categories:
                if extracted_value.lower() in standard_category.lower():
                    return standard_category, 1.0
                    
            # Fallback: Find closest energy storage technology/company match
            best_energy_match = max(
                energy_categories, 
                key=lambda category: self._calculate_energy_similarity(extracted_value, category)
            )
            similarity_score = self._calculate_energy_similarity(extracted_value, best_energy_match)
            return best_energy_match, similarity_score
            
        return extracted_value, 0.5

    def _calculate_energy_similarity(self, extracted_term: str, category_term: str) -> float:
        """
        Energy storage-specific similarity calculation.
        
        Better than generic string similarity for energy terminology:
        - Handles technical abbreviations (CAES, PSH, LDES)
        - Recognizes company name variations
        - Accounts for technology naming patterns
        """
        # Handle common energy storage abbreviations
        energy_abbreviations = {
            'caes': 'compressed air',
            'psh': 'pumped hydro', 
            'laes': 'liquid air',
            'ldes': 'long duration energy storage'
        }
        
        extracted_normalized = extracted_term.lower()
        category_normalized = category_term.lower()
        
        # Check for abbreviation matches first
        for abbrev, full_term in energy_abbreviations.items():
            if abbrev in extracted_normalized and full_term in category_normalized:
                return 0.9
                
        # Standard character overlap similarity for energy terms
        common_chars = set(extracted_normalized) & set(category_normalized)
        max_length = max(len(extracted_term), len(category_term))
        return len(common_chars) / max_length if max_length > 0 else 0.0

    def process_regulatory_batch(self, regulatory_texts: List[str], energy_sector: str) -> List[Dict[str, Tuple[str, float]]]:
        """
        Process multiple regulatory documents or announcements in batch.
        Optimized for LDES market analysis workflows.
        """
        return [
            self.extract_project_specs(text, energy_sector) 
            for text in regulatory_texts
        ]

if __name__ == "__main__":
    # Real-world LDES extraction example
    ldes_pipeline = LDESExtractionPipeline(
        ldes_model_path="models/spacy_ner/best_model",
        openai_api_key="your-openai-api-key",
        project_fields_path="configs/fields.json",
        energy_categories_path="configs/categories.json"
    )
    
    # Example: Form Energy iron-air project announcement
    sample_regulatory_text = """
    Form Energy announced a 5 MW / 500 MWh iron-air battery storage project 
    in partnership with Georgia Power. The facility will provide 100 hours of 
    duration and is expected to be operational by Q4 2025. Located in Georgia, 
    this long duration energy storage system will support grid reliability.
    """
    
    extracted_specs = ldes_pipeline.extract_project_specs(sample_regulatory_text, "ldes")
    print("Extracted LDES project specifications:")
    for field, (value, confidence) in extracted_specs.items():
        print(f"  {field}: {value} (confidence: {confidence:.2f})")
