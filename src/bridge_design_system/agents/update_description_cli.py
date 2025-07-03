import json
import os

json_path = os.path.join(os.path.dirname(__file__), '../data/all_categories.json')
json_path = os.path.abspath(json_path)

# Load the JSON data
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Show available categories
print("Available categories:", list(data.keys()))
category = input("Enter the category to update (e.g., triangle): ").strip()
if category not in data or not data[category]:
    print("Category not found or empty.")
    exit(1)

# Show available objects in the category (first 5 for preview)
for idx, obj in enumerate(data[category][:5]):
    print(f"{idx}: id={obj.get('id')}, description={obj.get('description', '')}")

index = int(input(f"Enter the index of the object to update (0-{len(data[category])-1}): "))
if not (0 <= index < len(data[category])):
    print("Invalid index.")
    exit(1)

desc = input("Enter your description: ")

# Update the description
old_desc = data[category][index].get("description", "")
data[category][index]["description"] = desc

# Save the updated JSON back to the file
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Description updated successfully! (Old: '{old_desc}' -> New: '{desc}')") 