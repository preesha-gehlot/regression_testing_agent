import json 
import yaml
import logging
from dotenv import load_dotenv
from input_data.req_doc import REQUIREMENTS_SPEC_DOC
from utils import validate_and_clean_json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

system_prompt="""
    You are an expert API tester tasked with creating a Postman Collection (v2.1.0) based on the 
    user's input. Your task is to understand an API endpoint using the OpenAPI 3.x specification and 
    Requirements Document provided by the user and then generate a Postman Collection tht achieves 
    maximum test coverage of the endpoint. 
    
    You are provided with an OpenAPI 3.x specification that outlines the structure of one 
    endpoint in the API, and a Requirements Document that outlines any changes across the entire API
    from the user.

    You must perform the following instructions:
    1. Understand the API endpoint structure using the OpenAPI specification (its inputs and ouputs)
    2. Determine whether any of the changes in the Requirement Document are related to this endpoint,
       if they are, update your understanding of the API endpoint structure to reflect these changes 
    3. Generate positive test cases for the endpoint:
        - There must be one test that uses all parameters at once 
        - For every parameter that is an enum, there must be one test case for every enum value. 
        - For every positive test, there must be a test script that checks the response status, 
          if the parameter value causes disambiguation it is 300, else it is 200.  
    4. Generate edge test cases for the endpoint:
        - For every parameter, generate a test case where it is empty
        - For every parameter, generate a test case where it is null
        - For every string parameter, create one test case where the string contains 
          special/unicode characters and escape sequences, and one case where the string is 
          only multiple whitespaces.  
        - For every integer parameter, generate test cases with negative values, decimals, the maximum 
          value + 1, and the minimum value - 1. 
        - For every parameter that is an email, date, URL or UUID generate a test with an invalid format
        - For every boolean and enum parameter, generate a test case where it is an invalid value 
        - For every array, object, and collection parameter, generate a test case where it is empty 
       Determine if each test case should pass (the test script should check for 200) or fail (the 
       test script should check for both 400 and 404).
    5. Present these test cases in a Postman collection. The output should only be the raw JSON 
       of the Postman collection. No explanations, markdown formatting or additional text. 
    
    <note>
        - Carefully read parameter descriptions in the OpenAPI specification and Requirements 
          document. If a parameter description mentions that certain values will "cause disambiguation"
          the test cases that have those values should expect a 300 status code response. 
        - For path parameters (parameters that are part of the URL path), use realistic example 
          values instead of variables. 
        - The url is provided as a variable called base_url and api_key is provided as a variable
          called app_key in Postman that can be used when generating the collection. 
        - No other variables are provided.  
    </note>

    Based on the OpenAPI specification and Requirements document create a Postman Collection that 
    ensures maximum test coverage, without adding unnecessary tests that cover the same test logic. 
    Present the collection in valid and complete JSON that can be imported directly into Postman. 
"""

def save_postman_collection_to_file(collection_json, filename) -> str:
    """
    Saves the Postman collection JSON to a file in the current directory.
    
    Args:
        collection_json (dict): The Postman collection JSON object
        tool_context (ToolContext): Provides access to session state for context
    
    Returns:
        str: The file path where the collection was saved
    """

    output_filename = "./output_data/" + Path(filename).stem + "_collection.json"
    
    # Save the collection to file
    with open(output_filename, 'w') as f:
        json.dump(collection_json, f, indent=2)
    
    return output_filename


def generate_postman_collection(client, filename):
    # Read JSON spec for singular endpoint
    with open(filename, 'r') as f:
        data = json.load(f)

    # Convert to JSON string
    OPENAPI_SPEC_DOC = json.dumps(data, indent=2)

    user_prompt=f"""
    OpenAPI specification :
    {OPENAPI_SPEC_DOC}
    Requirements Document :
    {REQUIREMENTS_SPEC_DOC}
    """

    try:
        logger.info("Sending conversion request to LLM...")
        # response = client.chat.completions.create(
        #     model="gpt-4o",
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_prompt}
        #     ],
        #     max_tokens=16384,  # Adjust based on your spec size
        #     response_format={"type": "json_object"}  # Ensures JSON output
        # )
        # Access the response content correctly
        # raw_text = response.choices[0].message.content

        # # Validate that the model returned valid JSON
        # postman_collection_json = json.loads(raw_text)

        #Correct way to send a message to Claude
        with client.messages.stream(
            model="claude-sonnet-4-20250514",  # or use "claude-sonnet-4-20250514" for Claude Sonnet 4
            max_tokens=30000,
            system=system_prompt,  # System prompt goes here, not in messages
            messages=[
                {"role": "user", "content": user_prompt}
            ]
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

        logger.info("Successfully converted spec to Postman collection with LLM.")

        # Save the result to the directory 
        save_postman_collection_to_file(postman_collection_json, filename)
        
        return {
            "status": "success",
            "message": "Conversion successful."
        }
    
    except Exception as e:
        message = f"An unexpected error occurred during OpenAI API call: {e}"
        logger.error(message)
        return {"status": "error", "message": message}



