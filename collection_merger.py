import json
import os
from pathlib import Path

def merge_postman_collections(collection_files, output_file="merged_collection.json"):
    """
    Merge multiple Postman collection files into a single collection.
    
    Args:
        collection_files: List of file paths to Postman collection JSON files
        output_file: Output file name for the merged collection
    """
    
    # Base template for the merged collection
    merged_collection = {
        "info": {
            "name": "Postman Collection",
            "description": "Comprehensive regression testing for a given API with maximum test coverage",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "base_url",
                "value": ""
            },
            {
                "key": "app_key",
                "value": ""
            }
        ]
    }
    
    # Array to store all items from all collections
    all_folders = []
    
    # Iterate through each collection file
    for file_path in collection_files:
        try:
            print(f"Processing: {file_path}")
            
            # Read the collection file
            with open(file_path, 'r', encoding='utf-8') as f:
                collection_data = json.load(f)
            
            # Extract the filename without extension for folder name
            filename = Path(file_path).stem
            
            # Extract items from the top-level "item" array
            if 'item' in collection_data and isinstance(collection_data['item'], list):
                items = collection_data['item']
                print(f"  Found {len(items)} items")

                # Create a folder for this collection's items
                folder = {
                    "name": filename,
                    "item": items,
                    "description": f"Tests from {file_path}",
                    "event": [],
                    "variable": []
                }
                
                # Add all items to our master array
                all_folders.append(folder)
            else:
                print(f"  Warning: No 'item' array found in {file_path}")
                
        except FileNotFoundError:
            print(f"  Error: File not found - {file_path}")
        except json.JSONDecodeError as e:
            print(f"  Error: Invalid JSON in {file_path} - {e}")
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
    
    # Populate the merged collection with all items
    merged_collection["item"] = all_folders
    
    # Write the merged collection to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_collection, f, indent=2, ensure_ascii=False)
        
        print(f"\nMerged collection created successfully!")
        print(f"  Output file: {output_file}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
