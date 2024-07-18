import spacy
import openai
import json
import logging
from typing import Dict, List, Tuple
from src.utils.helpers import clean_text, standardize_company_name
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NERPipeline:
    def __init__(self, spacy_model_path: str, openai_api_key: str, fields_path: str, categories_path: str, openai_model: str = "gpt-3.5-turbo"):
        self.nlp = spacy.load(spacy_model_path)
        openai.api_key = openai_api_key
        self.openai_model = openai_model
        
        # Load fields and categories
        with open(fields_path, 'r') as f:
            self.fields = json.load(f)
        with open(categories_path, 'r') as f:
            self.categories = json.load(f)

    def extract_entities(self, text: str, sector: str) -> Dict[str, Tuple[str, float]]:
        entities = {}
        
        # Use spaCy for initial NER
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in self.fields:
                entities[ent.label_] = (clean_text(ent.text), ent._.conf)

        # Use GPT-3 for any missing entities or refinement
        gpt3_entities = self._gpt3_extraction(text, entities, sector)
        entities.update(gpt3_entities)

        # Post-process entities
        for field, (value, conf) in entities.items():
            if field in self.fields:
                if self.fields[field] == "categorical":
                    matched_category, match_conf = self._match_category(field, value)
                    entities[field] = (matched_category, min(conf, match_conf))
            if field == "Developer":
                entities[field] = (standardize_company_name(value), conf)

        return entities

    @lru_cache(maxsize=100)
    def _gpt3_extraction(self, text: str, existing_entities: frozenset, sector: str) -> Dict[str, Tuple[str, float]]:
        prompt = f"""
        Extract the following entities from the text if not already found:
        {', '.join(self.fields.keys())}

        For sector: {sector}

        Existing entities: {dict(existing_entities)}

        Text: {text}

        Respond in JSON format. For categorical fields, provide the exact category if possible. Include a confidence score (0-1) for each extraction.
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts specific information from text."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response['choices'][0]['message']['content']
            extracted = json.loads(content)
            return {k: (v['value'], v['confidence']) for k, v in extracted.items()}
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from GPT-3 response: {content}")
            return {}
        except openai.error.OpenAIError as e:
            logging.error(f"OpenAI API error: {str(e)}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error in GPT-3 extraction: {str(e)}")
            return {}

    def _match_category(self, field: str, value: str) -> Tuple[str, float]:
        if field in self.categories:
            for category in self.categories[field]:
                if value.lower() in category.lower():
                    return category, 1.0
            # If no exact match, find the closest match
            closest_match = max(self.categories[field], key=lambda x: self._similarity(value, x))
            similarity = self._similarity(value, closest_match)
            return closest_match, similarity
        return value, 0.5

    def _similarity(self, s1: str, s2: str) -> float:
        # TODO
        # Implement a string similarity measure here
        return len(set(s1.lower()) & set(s2.lower())) / max(len(s1), len(s2))

    def process_batch(self, texts: List[str], sector: str) -> List[Dict[str, Tuple[str, float]]]:
        return [self.extract_entities(text, sector) for text in texts]

if __name__ == "__main__":
    # Example usage
    pipeline = NERPipeline(
        "path/to/spacy/model", 
        "your-openai-api-key",
        "path/to/fields.json",
        "path/to/categories.json"
    )
    text = "Project Alpha, a 100 MWh energy storage facility, was announced by GreenEnergy Corp. Located in California, the project is expected to be completed by 2025."
    entities = pipeline.extract_entities(text, "ldes")
    print(entities)

    # Batch processing example
    texts = [
        "Project Alpha, a 100 MWh energy storage facility, was announced by GreenEnergy Corp. Located in California, the project is expected to be completed by 2025.",
        "Project Beta, a 50 MW wind farm, is being developed by WindPower Inc. in Texas. Construction is set to begin in 2024."
    ]
    batch_results = pipeline.process_batch(texts, "ldes")
    for result in batch_results:
        print(result)
