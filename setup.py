from setuptools import setup, find_packages

setup(
    name="ldes_data_pipeline",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "PyPDF2==3.0.1",
        "spacy==3.5.3",
        "transformers==4.29.2",
        "torch==2.0.1",
        "pandas==2.0.2",
        "scikit-learn==1.2.2",
        "tqdm==4.65.0",
        "pyyaml==6.0",
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "openai==0.27.8"
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-based data structuring pipeline for LDES projects",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ldes_data_pipeline",
)