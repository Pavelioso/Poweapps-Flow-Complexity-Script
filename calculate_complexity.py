import os
import json
import csv
import re
import argparse

# Parse the directory input from the command line
parser = argparse.ArgumentParser(description="Process workflow JSON files to calculate complexity.")
parser.add_argument("workflow_directory", type=str, help="Directory containing the workflow JSON files")
args = parser.parse_args()
workflow_directory = args.workflow_directory

# Initialize a dictionary to store the points for each type defined in the CSV file
type_complexity = {}
type_count_template = {}

# Load complexity points and initialize counts from a CSV file 'points.csv'
csv_file = "points.csv"
with open(csv_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        type_name = row['type']
        complexity = row['complexity']
        if not complexity.isdigit():
            print(f"Warning: Non-integer value '{complexity}' found for type '{type_name}' in points.csv")
            continue
        type_complexity[type_name] = int(complexity)
        type_count_template[type_name] = 0

# Function to count occurrences of each type and calculate the total points
def count_and_calculate_complexity(data, type_count):
    total_points = 0
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "type" and value in type_count:
                type_count[value] += 1
                total_points += type_complexity.get(value, 0)
            else:
                total_points += count_and_calculate_complexity(value, type_count)
    elif isinstance(data, list):
        for item in data:
            total_points += count_and_calculate_complexity(item, type_count)

    return total_points

# Function to detect if a "Foreach" is nested within another "Foreach" - Seems to be very heavy inside of Powerapps Flows.
def is_loop_within_loop(data, inside_foreach=False):
    if isinstance(data, dict):
        if data.get("type") == "Foreach":
            if inside_foreach:
                return True
            inside_foreach = True

        for key, value in data.items():
            if is_loop_within_loop(value, inside_foreach):
                return True

    elif isinstance(data, list):
        for item in data:
            if is_loop_within_loop(item, inside_foreach):
                return True

    return False

# Make sure that provided directory exists before scanning it
all_results = []
if os.path.isdir(workflow_directory):
    json_files = [file for file in os.listdir(workflow_directory) if file.endswith('.json')]

    # Regular expression pattern to extract the file name and hash
    pattern = r"^(.*)-([A-F0-9\-]{36,42})\.json$"

    # Iterate through each JSON file and count occurrences
    for json_file in json_files:
        match = re.match(pattern, json_file)
        if not match:
            continue

        name, file_hash = match.groups()

        # Construct the full path to the JSON file
        json_path = os.path.join(workflow_directory, json_file)

        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Remove "triggers" and "definition" before processing
        json_data.pop("triggers", None)
        json_data.pop("definition", None)

        # Initialize type counts for each file separately to avoid overwriting counts
        type_count = type_count_template.copy()

        # Count the occurrences and calculate the total complexity points
        total_points = count_and_calculate_complexity(json_data, type_count)
        nested_loops_present = is_loop_within_loop(json_data)

        # Prepare the result for this file
        result = {
            "File": json_file,
            "Name": name,
            "Hash": file_hash,
            "TotalComplexityPoints": total_points,
            "IsLoopWithinLoopPresent": nested_loops_present,
        }
        result.update(type_count)
        all_results.append(result)

# Write all results to a single `output.csv` file
output_file = "output/complexity.csv"
fieldnames = ["File", "Name", "Hash", "TotalComplexityPoints", "IsLoopWithinLoopPresent"] + list(type_count_template.keys())

with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_results)

print(f"All results written to {output_file}")
