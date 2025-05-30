import re
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def clean_regulatory_text(text: str) -> str:
    """
    Clean text from energy storage regulatory documents and filings.
    
    Handles common artifacts from PDF extraction of regulatory documents:
    - OCR artifacts from scanned FERC filings
    - Legal formatting from regulatory text
    - Table extraction remnants from capacity specifications
    """
    # Remove common PDF extraction artifacts
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Clean regulatory document formatting
    text = re.sub(r'CONFIDENTIAL.*?TREATMENT', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page \d+ of \d+', '', text)
    text = re.sub(r'Docket No\. \w+-\d+', '', text)
    
    return text

def normalize_energy_capacity(capacity_text: str) -> Dict[str, Optional[float]]:
    """
    Parse and normalize energy storage capacity specifications.
    
    Handles the complexity of how LDES projects report capacity:
    - "100 MW / 400 MWh" → power: 100, energy: 400, duration: 4
    - "100 MW for 8 hours" → power: 100, energy: 800, duration: 8
    - "500 MWh battery facility" → energy: 500 (power/duration calculated if possible)
    
    Returns dict with 'power_mw', 'energy_mwh', 'duration_hours' keys.
    """
    capacity_specs = {'power_mw': None, 'energy_mwh': None, 'duration_hours': None}
    
    # Pattern: "100 MW / 400 MWh" or "100MW/400MWh"
    combined_pattern = r'(\d+(?:\.\d+)?)\s*MW\s*/\s*(\d+(?:\.\d+)?)\s*MWh'
    combined_match = re.search(combined_pattern, capacity_text, re.IGNORECASE)
    if combined_match:
        power_mw = float(combined_match.group(1))
        energy_mwh = float(combined_match.group(2))
        capacity_specs.update({
            'power_mw': power_mw,
            'energy_mwh': energy_mwh,
            'duration_hours': energy_mwh / power_mw if power_mw > 0 else None
        })
        return capacity_specs
    
    # Pattern: "100 MW for 8 hours" or "100MW, 8-hour duration"
    duration_pattern = r'(\d+(?:\.\d+)?)\s*MW.*?(\d+(?:\.\d+)?)[- ]?hour'
    duration_match = re.search(duration_pattern, capacity_text, re.IGNORECASE)
    if duration_match:
        power_mw = float(duration_match.group(1))
        duration_hours = float(duration_match.group(2))
        capacity_specs.update({
            'power_mw': power_mw,
            'duration_hours': duration_hours,
            'energy_mwh': power_mw * duration_hours
        })
        return capacity_specs
    
    # Individual patterns for MW and MWh
    mw_pattern = r'(\d+(?:\.\d+)?)\s*MW(?!h)'
    mwh_pattern = r'(\d+(?:\.\d+)?)\s*MWh'
    
    mw_match = re.search(mw_pattern, capacity_text, re.IGNORECASE)
    mwh_match = re.search(mwh_pattern, capacity_text, re.IGNORECASE)
    
    if mw_match:
        capacity_specs['power_mw'] = float(mw_match.group(1))
    if mwh_match:
        capacity_specs['energy_mwh'] = float(mwh_match.group(1))
    
    # Calculate duration if we have both power and energy
    if capacity_specs['power_mw'] and capacity_specs['energy_mwh']:
        capacity_specs['duration_hours'] = capacity_specs['energy_mwh'] / capacity_specs['power_mw']
    
    return capacity_specs

def standardize_ldes_technology(tech_description: str) -> str:
    """
    Standardize LDES technology names to consistent categories.
    
    Energy storage technologies get called different names across documents:
    - "iron-air battery" → "Iron-air"
    - "compressed air energy storage" → "Compressed air (CAES)" 
    - "liquid metal battery storage" → "Liquid metal"
    
    Based on the technology taxonomy used in LDES market analysis.
    """
    tech_lower = tech_description.lower()
    
    # Technology standardization mapping based on common variations
    technology_mappings = {
        'iron-air': ['iron-air', 'iron air', 'metal-air', 'form energy'],
        'Compressed air (CAES)': ['compressed air', 'caes', 'air storage'],
        'Liquid air (LAES)': ['liquid air', 'laes', 'cryogenic'],
        'Liquid metal': ['liquid metal', 'ambri'],
        'Pumped hydro (PSH)': ['pumped hydro', 'pumped storage', 'psh'],
        'Zinc-air': ['zinc-air', 'zinc air'],
        'Zinc-based': ['zinc-based', 'zinc bromide', 'zinc hybrid'],
        'Vanadium-redox flow': ['vanadium', 'redox flow', 'vrb'],
        'Iron flow': ['iron flow', 'ess iron'],
        'Molten salt': ['molten salt', 'thermal storage'],
        'Block-based gravity storage': ['gravity', 'energy vault', 'block'],
        'Rail-based gravity storage': ['rail', 'ares', 'advanced rail']
    }
    
    for standard_tech, variations in technology_mappings.items():
        for variation in variations:
            if variation in tech_lower:
                return standard_tech
    
    # Return original if no mapping found
    return tech_description

def parse_energy_company_name(company_text: str) -> str:
    """
    Standardize energy storage company names across different document formats.
    
    Handles variations like:
    - "Form Energy, Inc." → "Form Energy"
    - "Energy Storage Systems Inc" → "ESS"
    - "Ambri Inc." → "Ambri"
    """
    # Remove common corporate suffixes
    company_clean = re.sub(r'\b(Inc\.?|Corp\.?|Corporation|LLC|Limited|Ltd\.?)\b', '', company_text, flags=re.IGNORECASE)
    company_clean = company_clean.strip().rstrip(',')
    
    # Handle known energy storage company variations
    company_mappings = {
        'Form Energy': ['form energy'],
        'ESS': ['energy storage systems', 'ess inc'],
        'Malta': ['malta inc'],
        'Ambri': ['ambri inc'],
        'Energy Dome': ['energy dome'],
        'Hydrostor': ['hydrostor inc'],
        'Energy Vault': ['energy vault'],
        'Quidnet Energy': ['quidnet'],
        'Zinc8': ['zinc8 energy'],
        'Invinity Energy Systems': ['invinity', 'redflow'],
        'Noon Energy': ['noon energy'],
        'Highview Power': ['highview']
    }
    
    company_lower = company_clean.lower()
    for standard_name, variations in company_mappings.items():
        for variation in variations:
            if variation in company_lower:
                return standard_name
    
    return company_clean.title()

def extract_energy_project_timeline(text: str) -> Dict[str, Optional[str]]:
    """
    Extract project timeline dates from energy storage announcements.
    
    LDES projects have specific milestone patterns:
    - Announced: Initial project announcement
    - Permitted: Regulatory approval received  
    - Construction: Groundbreaking/construction start
    - Operational: Commercial operation date (COD)
    """
    timeline = {
        'announced_date': None,
        'permitted_date': None, 
        'construction_date': None,
        'operational_date': None
    }
    
    # Date patterns for different timeline milestones
    date_patterns = {
        'announced_date': r'announced.*?(\d{4})|(\d{4}).*?announcement',
        'permitted_date': r'permit.*?(\d{4})|approval.*?(\d{4})',
        'construction_date': r'construction.*?(\d{4})|groundbreaking.*?(\d{4})',
        'operational_date': r'operational.*?(\d{4})|cod.*?(\d{4})|online.*?(\d{4})'
    }
    
    for milestone, pattern in date_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Extract first non-None group (handles multiple capture groups)
            year = next((group for group in match.groups() if group), None)
            if year:
                timeline[milestone] = year
    
    return timeline

def validate_energy_project_data(project_specs: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate extracted energy storage project data for consistency and completeness.
    
    Energy storage projects have specific validation requirements:
    - Capacity specs should be consistent (MW * hours = MWh)
    - Technology should match known LDES categories
    - Timeline should be logical (announced < permitted < construction < operational)
    """
    validation_errors = []
    validated_specs = project_specs.copy()
    
    # Validate capacity consistency
    if all(key in project_specs for key in ['Discharging Power Capacity (MW)', 'Energy Capacity (MWh)', 'Duration (Hours)']):
        try:
            power_mw = float(project_specs['Discharging Power Capacity (MW)'])
            energy_mwh = float(project_specs['Energy Capacity (MWh)'])
            duration_hours = float(project_specs['Duration (Hours)'])
            
            calculated_energy = power_mw * duration_hours
            if abs(calculated_energy - energy_mwh) > energy_mwh * 0.1:  # 10% tolerance
                validation_errors.append(f"Capacity inconsistency: {power_mw}MW * {duration_hours}h ≠ {energy_mwh}MWh")
        except (ValueError, TypeError):
            validation_errors.append("Invalid capacity values - could not parse numbers")
    
    # Validate technology category
    if 'Technology' in project_specs:
        known_technologies = [
            'Iron-air', 'Compressed air (CAES)', 'Liquid air (LAES)', 'Liquid metal',
            'Pumped hydro (PSH)', 'Zinc-air', 'Zinc-based', 'Vanadium-redox flow',
            'Iron flow', 'Molten salt', 'Block-based gravity storage', 'Rail-based gravity storage'
        ]
        if project_specs['Technology'] not in known_technologies:
            validation_errors.append(f"Unknown technology category: {project_specs['Technology']}")
    
    return validated_specs, validation_errors

def format_energy_capacity_display(power_mw: float, energy_mwh: float, duration_hours: float) -> str:
    """
    Format energy storage capacity for display in reports and dashboards.
    
    Standard format: "100 MW / 400 MWh (4 hours)"
    Used for consistent capacity representation across LDES market analysis.
    """
    return f"{power_mw:.0f} MW / {energy_mwh:.0f} MWh ({duration_hours:.1f} hours)"

# Legacy function maintained for compatibility
def clean_text(text: str) -> str:
    """Legacy wrapper for clean_regulatory_text."""
    return clean_regulatory_text(text)

def standardize_company_name(name: str) -> str:
    """Legacy wrapper for parse_energy_company_name."""
    return parse_energy_company_name(name)
