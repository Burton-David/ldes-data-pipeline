# TODO run unit tests
# probably needs to be more restrictive
import re
import json
from typing import Dict, Any, List, Tuple
from dateutil.parser import parse as date_parse
from dateutil.parser._parser import ParserError
from pint import UnitRegistry

# Load fields and categories
with open('configs/fields.json', 'r') as f:
    FIELDS = json.load(f)

with open('configs/categories.json', 'r') as f:
    CATEGORIES = json.load(f)

ureg = UnitRegistry()

def validate_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Validate the cleaned data."""
    validated_data = {}
    errors = []

    for key, value in data.items():
        if key not in FIELDS:
            errors.append(f"Unknown field: {key}")
            continue

        field_type = FIELDS[key]

        if field_type == 'direct':
            if value:  # Allow any non-empty value
                validated_data[key] = value
            else:
                errors.append(f"Empty value for {key}")

        elif field_type == 'categorical':
            if key in CATEGORIES:
                if any(category.lower() in value.lower() for category in CATEGORIES[key]):
                    validated_data[key] = value
                else:
                    errors.append(f"Invalid category for {key}: {value}")
            else:
                errors.append(f"No categories defined for {key}")

        elif 'date' in key.lower():
            try:
                parsed_date = date_parse(value)
                validated_data[key] = parsed_date.strftime("%Y-%m-%d")
            except ParserError:
                errors.append(f"Invalid date for {key}: {value}")

        elif 'capacity' in key.lower():
            try:
                quantity = ureg.Quantity(value)
                if quantity.dimensionality == ureg.MW.dimensionality:
                    validated_data[key] = f"{quantity.magnitude:.2f} {quantity.units}"
                else:
                    errors.append(f"Invalid unit for {key}: {value}")
            except:
                errors.append(f"Invalid capacity for {key}: {value}")

        elif 'cost' in key.lower():
            try:
                # Remove currency symbols and 'M' for million
                clean_value = re.sub(r'[^\d.]', '', value.replace('M', ''))
                cost = float(clean_value)
                validated_data[key] = f"${cost:.2f}M"
            except ValueError:
                errors.append(f"Invalid cost for {key}: {value}")

        else:
            # For any other keys, just pass them through
            validated_data[key] = value

    return validated_data, errors

if __name__ == "__main__":
    # Test the function
    test_data = {
        "Project name": "Project Alpha",
        "Energy Capacity (MWh)": "100.0 MWh",
        "Announced date": "May 15, 2023",
        "Location": "California, USA",
        "Developer": "GreenEnergy Corp",
        "Technology": "Pumped hydro",
        "Total Cost (Capex)": "$50M"
    }
    validated, errors = validate_data(test_data)
    print("Validated data:", validated)
    print("Errors:", errors)
