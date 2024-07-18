import re
import json
from typing import Dict, List

# Load fields and categories
with open('configs/fields.json', 'r') as f:
    FIELDS = json.load(f)

with open('configs/categories.json', 'r') as f:
    CATEGORIES = json.load(f)

def apply_rules(text: str) -> Dict[str, str]:
    """Apply rule-based extraction to the text."""
    entities = {}
    
    # Extract project name
    project_name_match = re.search(r'(?:Project|project)\s+([A-Z][a-z]+(?: [A-Z][a-z]+)*)', text)
    if project_name_match:
        entities['Project name'] = project_name_match.group(1)
    
    # Extract capacity
    capacity_match = re.search(r'(\d+(?:\.\d+)?\s*(?:MW|MWh))', text, re.IGNORECASE)
    if capacity_match:
        capacity = capacity_match.group(1)
        if 'MWh' in capacity:
            entities['Energy Capacity (MWh)'] = capacity
        else:
            entities['Discharging Power Capacity (MW)'] = capacity
    
    # Extract location
    location_match = re.search(r'in\s+([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,\s+[A-Z]{2})?)', text)
    if location_match:
        entities['Location'] = location_match.group(1)
    
    # Extract year
    year_match = re.search(r'\b(20\d{2})\b', text)
    if year_match:
        entities['Expected COD year'] = year_match.group(1)
    
    # Extract company name
    company_match = re.search(r'by\s+([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:\s+(?:Corp|Inc|LLC|Ltd)\.?)?)', text)
    if company_match:
        entities['Developer'] = company_match.group(1)
    
    return entities

def extract_technologies(text: str) -> List[str]:
    """Extract potential technologies mentioned in the text."""
    return [tech for tech in CATEGORIES['Technology'] if tech.lower() in text.lower()]

def categorize_entities(entities: Dict[str, str]) -> Dict[str, str]:
    """Categorize extracted entities based on the predefined categories."""
    categorized = {}
    for field, value in entities.items():
        if field in FIELDS and FIELDS[field] == 'categorical':
            if field in CATEGORIES:
                for category in CATEGORIES[field]:
                    if value.lower() in category.lower():
                        categorized[field] = category
                        break
                if field not in categorized:
                    categorized[field] = value  # Use original value if no match found
        else:
            categorized[field] = value
    return categorized

if __name__ == "__main__":
    # Test the functions
    test_text = "Project Alpha, a 100 MWh battery storage facility by GreenEnergy Corp., will be built in California, USA by 2025."
    extracted = apply_rules(test_text)
    print("Extracted entities:", extracted)
    print("Technologies:", extract_technologies(test_text))
    print("Categorized entities:", categorize_entities(extracted))