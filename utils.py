
import logging
import json 
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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