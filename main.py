from reference_resolver import process_all_endpoints
from collection_merger import merge_postman_collections
from postman_generation_agent import generate_postman_collection
import yaml
from openai import OpenAI
import anthropic  
import logging
from dotenv import load_dotenv 
from pathlib import Path
import os
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

SPECIFICATION_FILE = './input_data/tfl_openapi_spec_multiple_api_old.yaml'

with open(SPECIFICATION_FILE, 'r') as f:
    spec = yaml.safe_load(f)

processed_endpoints = process_all_endpoints(spec)

try:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Required environment variable not set: ANTHROPIC_API_KEY")
    # client = OpenAI(api_key=api_key)
    client = anthropic.Anthropic(api_key=api_key)
except ValueError as e:
    logger.error(f"API configuration failed: {e}")


endpoint_files = [str(f) for f in Path("./endpoint_specs").glob('*.json')]
if endpoint_files:
    for file in endpoint_files:
        generate_postman_collection(client, file)
else:
    print("No endpoint spec files found!")

collection_files = [str(f) for f in Path("./output_data").glob('*.json')]
# print(collection_files)    
if collection_files:
    merge_postman_collections(collection_files, "./output_data/merged_regression_collection.json")
else:
    print("No Postman collection files found!")