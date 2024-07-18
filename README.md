# LDES Data Structuring Pipeline

## Project Overview

This project implements an AI-based data structuring pipeline for Long Duration Energy Storage (LDES) projects and other sectors of the climate economy. It ingests data from various sources (news articles, press releases, regulatory filings), processes it using NLP techniques, and structures it for further analysis.

## Features

- Data ingestion from multiple sources (URLs, PDFs, HTML)
- Named Entity Recognition (NER) using custom-trained spaCy models
- GPT-3 integration for advanced text analysis
- Rule-based extraction for specific data points
- Flexible pipeline design to accommodate multiple sectors
- Scalable processing with asyncio for concurrent operations
- Database integration for structured data storage
- Configurable via YAML files

## Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key (for GPT-3 integration)

## Installation

1. Clone the repository:
`git clone https://github.com/yourusername/ldes-data-pipeline.git
cd ldes-data-pipeline`
2. Create and activate a virtual environment:
`python -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate`
3. Install the required packages:
`pip install -r requirements.txt`
4. Set up the database:
- Create a PostgreSQL database
- Update the database configuration in `config.yaml`

5. Set up environment variables:
- Create a `.env` file in the project root
- Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

## Configuration

The project uses a `config.yaml` file for configuration. Key settings include:

- Database connection details
- Data directory paths
- Ingestion settings (URL columns, chunk size, etc.)
- Model paths and settings

Modify `config.yaml` to suit your specific setup and requirements.

## Usage

1. Data Ingestion:
`python src/data/ingestion.py`
This script will process URLs from the specified CSV file and save the extracted content.

2. Run the full pipeline:
`python main.py`
This will process the ingested data, perform NER, apply rules, and store the structured data in the database.

## Project Structure
ldes-data-pipeline/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── annotated/
│
├── models/
│   └── spacy_ner/
│
├── src/
│   ├── data/
│   │   ├── ingestion.py
│   │   └── annotation.py
│   ├── pipeline/
│   │   ├── ner_pipeline.py
│   │   ├── rule_based_extraction.py
│   │   ├── data_cleaning.py
│   │   └── data_validation.py
│   ├── database/
│   │   └── db_operations.py
│   └── utils/
│       └── helpers.py
│
├── configs/
│   ├── config.yaml
│   ├── fields.json
│   └── categories.json
│
├── tests/
│
├── logs/
│
├── requirements.txt
├── main.py
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
└── README.md
## Testing

Run the test suite:
`python -m unittest discover tests`
## Deployment

The project includes a Dockerfile and docker-compose.yml for containerized deployment. To build and run:
`docker-compose up --build`
For CI/CD, a Jenkinsfile is provided. Set up a Jenkins pipeline using this file for automated testing and deployment.

## Adding New Data Types

To add support for new sectors or data types:

1. Update `configs/fields.json` with new fields
2. Update `configs/categories.json` if new categorical data is needed
3. Modify the NER pipeline in `src/pipeline/ner_pipeline.py` if necessary
4. Add any new rule-based extractions to `src/pipeline/rule_based_extraction.py`
