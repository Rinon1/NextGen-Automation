import os
import json
import re # This is needed for the filename cleaning logic

# --- Configuration ---
SOURCE_FOLDER = '.' 
OUTPUT_FILE = 'processed_workflows_v2.jsonl'
# ---------------------

def extract_info_from_workflow(filepath):
    """Extracts key technical details from a single n8n workflow JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        workflow_name = data.get('name', 'Unnamed Workflow')
        nodes = data.get('nodes', [])
        node_names = sorted(list(set([node.get('name', '') for node in nodes if node.get('name')])))
        return {
            "workflow_name": workflow_name,
            "node_names": node_names
        }
    except Exception as e:
        print(f"  [Warning] Could not parse JSON file {filepath}: {e}")
        return None

def generate_templated_description(workflow_info):
    """Creates a simple, rule-based description from workflow info."""
    name = workflow_info['workflow_name']
    nodes = workflow_info['node_names']
    
    description = f"This is an automated workflow named '{name}'."
    if nodes:
        node_list_str = ", ".join(nodes)
        description += f" It connects and automates the following tools or steps: {node_list_str}."
    else:
        description += " It does not have any named nodes defined."
        
    return description

# --- Main Script ---
print(f"Starting data preparation...")

all_workflows_data = []
processed_count = 0

for foldername, subfolders, filenames in os.walk(SOURCE_FOLDER):
    json_files_in_folder = [f for f in filenames if f.lower().endswith('.json')]
    if not json_files_in_folder:
        continue

    print(f"Scanning folder: {foldername}")

    readme_content = ""
    readme_path = os.path.join(foldername, 'README.txt')
    if os.path.exists(readme_path):
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read().strip()
                print(f"  - Found custom description in README.txt")
        except Exception as e:
            print(f"  [Warning] Could not read README.txt: {e}")

    for json_file in json_files_in_folder:
        # Skip this script and the output file
        if json_file == os.path.basename(__file__) or json_file == OUTPUT_FILE:
            continue
            
        json_path = os.path.join(foldername, json_file)
        workflow_info = extract_info_from_workflow(json_path)
        
        if workflow_info:
            final_description = readme_content
            if not final_description:
                final_description = generate_templated_description(workflow_info)
                print(f"  - Generated a description for {json_file}")

            # ================================================================= #
            #                          CORRECTED BLOCK                          #
            # ================================================================= #
            # This block now correctly generates the download URL.
            
            # 1. Your R2 public URL
            R2_PUBLIC_URL = "https://pub-2f7370fd7b2c4f79969d428dc6910b02.r2.dev" 

            # 2. Get the clean, sanitized filename to match what's in R2
            # This logic is from the renaming script to ensure they match perfectly.
            base_name, extension = os.path.splitext(os.path.basename(json_path))
            base_name = re.sub(r'[_\s\+&]+', '_', base_name)
            base_name = re.sub(r'[^a-zA-Z0-9_-]', '', base_name)
            sanitized_filename = f"{base_name.lower()}{extension.lower()}"
            
            # 3. Create the final record, including the all-important download_url
            final_record = {
                "source_file": json_path,
                "name": workflow_info['workflow_name'],
                "description": final_description,
                "nodes": workflow_info['node_names'],
                "download_url": f"{R2_PUBLIC_URL}/{sanitized_filename}" # <-- The URL is now added here
            }
            
            all_workflows_data.append(final_record)
            processed_count += 1
            # ================================================================= #

# --- Write the final consolidated file ---
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for record in all_workflows_data:
        f.write(json.dumps(record) + '\n')

print(f"\n--- DONE ---")
print(f"Successfully processed {processed_count} workflow files.")
print(f"Your consolidated knowledge base is ready at: {OUTPUT_FILE}")