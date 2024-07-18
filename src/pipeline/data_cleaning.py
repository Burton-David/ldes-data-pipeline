# TODO
# Add more field types and corresponding functions as needed
# Currently minimal checks will update as notice junk slipping through
import re
import json
from typing import Dict, Any
from datetime import datetime

# Load fields
with open('configs/fields.json', 'r') as f:
    FIELDS = json.load(f)

def get_cleaning_function(field_type):
    cleaning_functions = {
        'date': standardize_date,
        'capacity': standardize_capacity,
        'cost': standardize_cost,
    }
    return cleaning_functions.get(field_type, lambda x: x)  # Default to identity function

def clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
    cleaned_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            value = re.sub(r'\s+', ' ', value).strip()
            if key in FIELDS:
                field_type = FIELDS[key]
                cleaning_func = get_cleaning_function(field_type)
                value = cleaning_func(value)
        cleaned_data[key] = value
    return cleaned_data

def standardize_date(date_str: str) -> str:
    """Standardize date to YYYY-MM-DD format."""
    try:
        # Try to parse the date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # If that fails, try a more flexible parsing
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            # If all parsing fails, return the original string
            return date_str

def standardize_capacity(capacity_str: str) -> str:
    """Standardize capacity to MWh format."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*(MW|MWh)', capacity_str, re.IGNORECASE)
    if match:
        value, unit = match.groups()
        return f"{float(value):.1f} {unit.upper()}"
    return capacity_str  # Return original if no pattern matches

def standardize_cost(cost_str: str) -> str:
    """Standardize cost to millions of dollars format."""
    match = re.search(r'(\d+(?:\.\d+)?)\s*(million|m|billion|b)?', cost_str, re.IGNORECASE)
    if match:
        value, unit = match.groups()
        value = float(value)
        if unit and unit.lower().startswith('b'):
            value *= 1000
        return f"${value:.2f}M"
    return cost_str  # Return original if no pattern matches

if __name__ == "__main__":
    # Test the functions
    test_data = {
        "Project name": "Project   Alpha",
        "Energy Capacity (MWh)": "100 MW",
        "Announced date": "5/15/2023",
        "Location": "california, USA",
        "Total Cost (Capex)": "50 million"
    }
    print(clean_data(test_data))
