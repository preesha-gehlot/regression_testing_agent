import os
import yaml
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def find_all_refs(obj):
    """Recursively find all $ref values in the object"""
    refs = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == '$ref' and isinstance(value, str):
                # Extract schema name from "#/components/schemas/SchemaName"
                if value.startswith('#/components/schemas/'):
                    schema_name = value.replace('#/components/schemas/', '')
                    refs.add(schema_name)
            else:
                refs.update(find_all_refs(value))
    elif isinstance(obj, list):
        for item in obj:
            refs.update(find_all_refs(item))
    
    return refs


def get_all_schema_dependencies(spec, initial_refs, visited=None, max_depth=10):
    """Recursively find all schema dependencies"""
    if visited is None:
        visited = set()
    
    all_refs = set(initial_refs)
    depth = 0
    # Use a queue to process references level by level
    to_process = list(initial_refs)
    
    while to_process and depth < max_depth:
        current_level = to_process.copy()
        to_process.clear()
        for ref in current_level:
            if ref in visited:
                continue

            visited.add(ref)

            # Check if the schema exists in the spec
            if ref in spec.get('components', {}).get('schemas', {}):
                schema = spec['components']['schemas'][ref]
                nested_refs = find_all_refs(schema)
                
                # Add new references to the set and queue for processing
                for nested_ref in nested_refs:
                    if nested_ref not in visited and nested_ref not in all_refs:
                        all_refs.add(nested_ref)
                        to_process.append(nested_ref)
            else:
                print(f"Warning: Referenced schema '{ref}' not found in components/schemas")
        
        depth += 1
    return all_refs


def extract_endpoint_info(spec, endpoint_path, method):
    """Extract a single endpoint with its dependencies"""
    endpoint = spec['paths'][endpoint_path][method]
    refs = find_all_refs(endpoint)
    
    # Need to recursively get all referenced schemas and their dependencies
    all_refs = get_all_schema_dependencies(spec, refs)
    
    # Build the mini spec with all required schemas
    schemas_dict = {}
    missing_schemas = []
    
    for ref in all_refs:
        if ref in spec.get('components', {}).get('schemas', {}):
            schemas_dict[ref] = spec['components']['schemas'][ref]
        else:
            missing_schemas.append(ref)
    
    if missing_schemas:
        print(f"Warning: Missing schemas for {endpoint_path} {method}: {missing_schemas}")
    
    mini_spec = {
        'openapi': spec['openapi'],
        'info': spec['info'], 
        'paths': {endpoint_path: {method: endpoint}},
        'components': {
            'schemas': schemas_dict
        }
    }
    
    return mini_spec

def validate_mini_spec(mini_spec, endpoint_path, method):
    """Validate that all references in the mini spec can be resolved"""
    all_refs = find_all_refs(mini_spec)
    available_schemas = set(mini_spec.get('components', {}).get('schemas', {}).keys())
    
    missing_refs = all_refs - available_schemas
    if missing_refs:
        print(f"ERROR: {method.upper()} {endpoint_path} has unresolved references: {missing_refs}")
        return False
    else:
        print(f"SUCCESS: {method.upper()} {endpoint_path} - all references resolved")
        return True

def save_endpoint_specs(processed_endpoints, output_dir="endpoint_specs"):
    """Save each endpoint to a separate YAML file"""
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    for endpoint_data in processed_endpoints:
        path = endpoint_data['path']
        method = endpoint_data['method']
        spec = endpoint_data['spec']
        is_valid = endpoint_data.get('is_valid', False)
        
        # Create safe filename from path and method
        # Replace / with _ and remove any problematic characters
        safe_path = path.replace('/', '_').replace('{', '').replace('}', '').strip('_')
        filename = f"{method.lower()}_{safe_path}.json"
        
        # Handle edge cases for filename
        if not safe_path:  # Root path "/"
            filename = f"{method.lower()}_root.json"
        
        filepath = os.path.join(output_dir, filename)
        
        # Save to JSON file
        with open(filepath, 'w') as f:
            json.dump(spec, f, indent=2)
        
        status = "✓" if is_valid else "✗"
        print(f"{status} Saved: {filepath}")


def process_all_endpoints(spec):
    """Process all endpoints in the spec"""
    inlined_endpoints = []
    
    for endpoint_path, methods in spec['paths'].items():
        for method, _ in methods.items():
            print(f"Processing {method.upper()} {endpoint_path}")
            
            # Extract endpoint with dependencies
            mini_spec = extract_endpoint_info(spec, endpoint_path, method)
            is_valid = validate_mini_spec(mini_spec, endpoint_path, method)
            inlined_endpoints.append({
                'path': endpoint_path,
                'method': method,
                'spec': mini_spec,
                'is_valid': is_valid
            })
    
    # Save all processed endpoints
    save_endpoint_specs(inlined_endpoints)
    
    return inlined_endpoints
