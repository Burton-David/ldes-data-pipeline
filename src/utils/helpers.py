import re
from typing import Dict, Any, List

def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text."""
    return re.sub(r'\s+', ' ', text).strip()

def validate_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean extracted entities."""
    valid_entities = {}
    for key, value in entities.items():
        if value and isinstance(value, str):
            valid_entities[key] = clean_text(value)
    return valid_entities

def format_capacity(capacity: str) -> str:
    """Format capacity to a standard format (e.g., '100 MWh')."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*(MW|MWh)', capacity, re.IGNORECASE)
    if match:
        value, unit = match.groups()
        return f"{float(value):.1f} {unit.upper()}"
    return capacity

def extract_dates(text: str) -> List[str]:
    """Extract dates from text."""
    date_pattern = r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{2,4}|\d{4})\b'
    return re.findall(date_pattern, text)

def standardize_company_name(name: str) -> str:
    """Standardize company name format."""
    replacements = {
        'Corp.': 'Corporation',
        'Inc.': 'Incorporated',
        'Ltd.': 'Limited',
        'LLC': 'Limited Liability Company'
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.title()