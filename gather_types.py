import os
import json
import argparse
import csv

# Parse the directory input from the command line
parser = argparse.ArgumentParser(description="Collect unique types from workflow (Powerautomate Flow) JSON files.")
parser.add_argument("workflow_directory", type=str, help="Directory containing the workflow JSON files")
args = parser.parse_args()
workflow_directory = args.workflow_directory

# Initialize an empty set to hold unique types
all_types = set()

# Recursive function to collect types from JSON data
def collect_types(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "type":
                all_types.add(value)
            collect_types(value)
    elif isinstance(data, list):
        for item in data:
            collect_types(item)

# Ensure the provided directory exists before scanning it
if os.path.isdir(workflow_directory):
    json_files = [file for file in os.listdir(workflow_directory) if file.endswith('.json')]

    # Process each JSON file and collect types
    for json_file in json_files:
        json_path = os.path.join(workflow_directory, json_file)
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        collect_types(json_data)

# Output all collected types
print("Unique types found:")
for type_name in sorted(all_types):
    print(type_name)

# Export the unique types to a CSV file with complexity placeholder (0)
csv_file_path = "output/found_types.csv"
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["type", "complexity"])  # Write header
    for type_name in sorted(all_types):
        complexity_placeholder = "0"
        csvwriter.writerow([type_name, complexity_placeholder])

print(f"Unique types have been written to {csv_file_path}")

