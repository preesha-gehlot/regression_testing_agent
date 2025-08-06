import json 
import os 
import anthropic  
import logging
from regression_testing.req_doc_multiple_api import REQUIREMENTS_SPEC_DOC
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

import yaml
import json

# Read YAML file and convert to JSON
with open('./tfl_openapi_spec_multiple_api_old.yaml', 'r') as yaml_file:
    data = yaml.safe_load(yaml_file)

# Convert to JSON string
OPENAPI_SPEC_DOC = json.dumps(data, indent=2)

system_prompt="""You are an expert API developer. Create a Postman Collection (v2.1.0) in JSON 
format from the provided OpenAPI 3.x specification and Requirements Document.

Requirements:
- Generate MAXIMUM TEST COVERAGE through comprehensive regression testing for every endpoint
- Focus on testing ALL possible edge cases and boundary conditions for input parameters
- Create extensive test variations, including POSITIVE and NEGATIVE test cases, covering:
    **Parameter Edge Cases:**
    - Minimum/Maximum values for numeric fields (0, -1, 999999999, etc.)
    - Boundary values for string lengths (empty, 1 char, max length, over max length)
    - Special characters and encoding (Unicode, symbols, escape sequences)
    - Format variations for emails, dates, URLs, UUIDs
    - Case sensitivity testing (uppercase, lowercase, mixed case)
    - Whitespace handling (leading/trailing spaces, tabs, newlines)
    
    **Data Type Variations:**
    - Valid and invalid data types for each parameter
    - Type coercion scenarios (string numbers, boolean strings)
    - Null, undefined, and missing parameter combinations
    - Empty arrays, objects, and collections

- Use the OpenAPI spec and Requirements Document modifications to ensure:
    - Correct request structures for all test variations
    - All parameter combinations are tested
    - Edge cases specific to business logic requirements are covered

Note: Focus on BREADTH over DEPTH
- Minimize test scripts - only basic status code validation (pm.test("Status code is X", () => pm.response.to.have.status(X)))

Output Format:
Return ONLY the raw JSON of the Postman collection. No explanations, markdown formatting, or additional text.
The url is stored as base_url and api key is stored as app_key variables in Postman, you can use them directly.  
There are NO OTHER variables set except for app_key and base_url.  
CRITICAL: The output MUST BE VALID, CORRECT JSON, that can be imported directly into Postman
"""

user_prompt=f"""
OpenAPI specification :
{OPENAPI_SPEC_DOC}
Requirements doc :
{REQUIREMENTS_SPEC_DOC}
"""

def save_postman_collection_to_file(collection_json: dict) -> str:
    """
    Saves the Postman collection JSON to a file in the current directory.
    
    Args:
        collection_json (dict): The Postman collection JSON object
        tool_context (ToolContext): Provides access to session state for context
    
    Returns:
        str: The file path where the collection was saved
    """
    
    # Create the postman collection filename
    output_filename = f"postman_collection_regression_testing.json"
    
    # Save the collection to file
    with open(output_filename, 'w') as f:
        json.dump(collection_json, f, indent=2)
    
    return output_filename

def validate_and_clean_json(response_text):
    """
    Clean and validate the JSON response
    """
    try:
        # Remove any markdown formatting if present
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if they exist
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]  # Remove ```json
        if cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]   # Remove ```
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]  # Remove trailing ```
        
        cleaned_text = cleaned_text.strip()
        
        # Validate JSON
        collection_json = json.loads(cleaned_text)
        
        logger.info("JSON validation successful")
        return collection_json
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.error(f"Problematic text around position {e.pos}: {response_text[max(0, e.pos-50):e.pos+50]}")
        
        # Try to fix common JSON issues
        return attempt_json_repair(cleaned_text)

def attempt_json_repair(text):
    """
    Attempt to repair common JSON formatting issues
    """
    try:
        # Common fixes
        fixes = [
            # Remove trailing commas
            lambda x: x.replace(',}', '}').replace(',]', ']'),
            # Fix unescaped quotes in strings
            lambda x: x.replace('\\"', '"'),
        ]
        
        for fix in fixes:
            try:
                fixed_text = fix(text)
                return json.loads(fixed_text)
            except:
                continue
                
        logger.error("Could not repair JSON")
        return None
        
    except Exception as e:
        logger.error(f"JSON repair failed: {e}")
        return None

def generate_postman_collection(client):
    try:
        logger.info("Sending conversion request to Claude 4 Sonnet...")
        # response = client.chat.completions.create(
        #     model="gpt-4o",
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ],
        #     max_tokens=4096,  # Adjust based on your spec size
        #     response_format={"type": "json_object"}  # Ensures JSON output
        # )

        # Use streaming to avoid timeout
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=25000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Lower temperature for more consistent JSON
        ) as stream:
            
            response_text = ""
            char_count = 0
            
            # Stream the response
            for text in stream.text_stream:
                response_text += text
                char_count += len(text)
                
                # Show progress every 5000 characters
                if char_count % 5000 == 0:
                    logger.info(f"Generated {char_count} characters...")
            
            logger.info(f"Streaming completed. Total characters: {len(response_text)}")
            
            # Validate and clean the JSON response
            postman_collection_json = validate_and_clean_json(response_text)
            
            if postman_collection_json is None:
                return {
                    "status": "error", 
                    "message": "Failed to parse JSON response from Claude"
                }
            
            logger.info("Successfully converted spec to Postman collection with Claude 4 Sonnet.")

            # Save the result to the directory 
            output_path = save_postman_collection_to_file(postman_collection_json)
            logger.info(f"Collection saved to: {output_path}")
            
            return {
                "status": "success",
                "message": "Conversion successful.",
                "output_file": output_path
            }
    
    except json.JSONDecodeError as e:
        message = f"Conversion failed: The model returned invalid JSON. Error: {e}"
        logger.error(message)
        return {"status": "error", "message": message}
    
    except Exception as e:
        message = f"An unexpected error occurred during Anthropic API call: {e}"
        logger.error(message)
        return {"status": "error", "message": message}

if __name__=="__main__":
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Required environment variable not set: ANTHROPIC_API_KEY")
        # client = OpenAI(api_key=api_key)
        client = anthropic.Anthropic(api_key=api_key)
    except ValueError as e:
        logger.error(f"OpenAI API configuration failed: {e}")
    
    generate_postman_collection(client)
