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

## Current Prototype Overview

### Architecture

The current prototype implements a modular pipeline for processing LDES and climate economy data:

1. **Data Ingestion**: Asyncio-based scraper for concurrent URL processing (`src/data/ingestion.py`)
2. **NER Pipeline**: Custom spaCy model combined with GPT-3 for entity extraction (`src/pipeline/ner_pipeline.py`)
3. **Database Operations**: PostgreSQL integration for data storage (`src/database/db_operations.py`)

### Key Components

- **Ingestion Module**: Capable of processing multiple URLs concurrently, extracting text from HTML and PDF sources.
- **NER Pipeline**: Utilizes a custom-trained spaCy model for initial entity recognition, supplemented by GPT-3 for refinement and handling complex extractions.
- **Configuration System**: YAML-based configuration for easy adjustment of pipeline parameters and database settings.
- **Data Models**: Defined in `configs/fields.json` and `configs/categories.json` for flexible entity definitions.

### Current Capabilities

- Concurrent processing of multiple data sources
- Entity extraction for LDES-specific fields (e.g., Project Name, Capacity, Location)
- Basic data cleaning and standardization
- Configurable pipeline for easy adaptation to new data types
- Database storage of processed entities

### Limitations and Future Work

- Rule-based extraction, advanced data cleaning, and validation are implemented but not yet integrated into the main pipeline.
- The system currently lacks comprehensive error handling and logging.
- Testing suite is in early stages and needs expansion.
- The prototype is not yet optimized for large-scale data processing.

### Next Steps

Immediate priorities for improving the prototype include:
1. Integration of rule-based extraction and advanced data cleaning into the main pipeline.
2. Implementation of comprehensive data validation.
3. Expansion of the testing suite for improved reliability.
4. Enhancement of error handling and logging for better debugging and monitoring.

For a full list of planned improvements, see the [To Do](#to-do) section.

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
# ldes-data-pipeline

**File Structure**

```plaintext
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
│   ├── configs/
│       ├── config.yaml
│       ├── fields.json
│       └── categories.json
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
```

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

## To Do
#### Integration and Functionality:

- Integrate rule-based extraction (src/pipeline/rule_based_extraction.py) into the main pipeline
- Implement and integrate data cleaning (src/pipeline/data_cleaning.py) into the processing flow
- Incorporate data validation (src/pipeline/data_validation.py) to ensure data quality


#### Testing:

- Develop unit tests for all major components (ingestion, NER, rule-based extraction, cleaning, validation)
- Create integration tests to ensure all parts of the pipeline work together
- Implement end-to-end tests to validate the entire process


#### Documentation:

- Expand the README.md with detailed setup instructions, usage examples, and project structure explanation
- Add docstrings to all functions and classes
- Create a user guide explaining how to use the pipeline and interpret results


#### Error Handling and Logging:

- Implement comprehensive error handling throughout the pipeline
- Set up detailed logging to track the processing of each document and any issues encountered


#### Performance Optimization:

- Profile the code to identify performance bottlenecks
- Implement batch processing for improved efficiency with large datasets
- Optimize database operations for faster data insertion and retrieval


#### Scalability:

- Implement a message queue system (e.g., RabbitMQ) for distributed processing
- Set up a worker system to handle tasks asynchronously


#### Data Management:

- Implement a data versioning system (e.g., DVC) to track changes in datasets
- Create a system for handling and storing large files that exceed GitHub's limits


#### Configuration and Flexibility:

- Expand the configuration system to allow easy addition of new data types and sectors
- Create a plugin system for adding new extraction methods or data sources


#### DevOps and Deployment:

- Refine the Jenkinsfile for a more robust CI/CD pipeline
- Optimize the Dockerfile and docker-compose.yml for production use
- Set up monitoring and alerting for the deployed system


#### Security:

- Implement proper secret management for API keys and database credentials
- Set up role-based access control for different parts of the system


#### User Interface:

- Develop a basic web interface for monitoring pipeline status and viewing results
- Create an API for programmatic access to the pipeline and results


#### Data Visualization:

- Implement basic data visualization tools to represent the extracted information


#### Extensibility:

- Create a framework for easily adding new AI models (beyond spaCy and GPT-3) to the pipeline


#### Performance Metrics:

- Implement a system to track and report on the accuracy and efficiency of the extraction process


#### Documentation and Knowledge Transfer:

- Create technical documentation detailing the system architecture and design decisions
- Prepare a presentation or demo video showcasing the pipeline's capabilities
