import json
from datetime import datetime

# Load the found material catalog
with open("src/bridge_design_system/data/found_material_catalog.json", "r") as f:
    found_data = json.load(f)

# Prepare new material entries
def get_dimensions_from_vertices(vertices):
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return {
        "length": round(max_x - min_x, 3),
        "width": round(max_y - min_y, 3),
        "height": None  # Fill in if you have Z or thickness info
    }

materials = []
for obj in found_data.get("catalog", []):
    dimensions = get_dimensions_from_vertices(obj["vertices"])
    material = {
        "material_id": obj["id"],
        "dimensions_mm": dimensions,
        "weight_kg": None,
        "density_kg_m3": None,
        "cuts": [],
        "waste_mm": 0,
        "utilization_percent": 0.0,
        "stiffness": "",
        "texture": "",
        "humidity": "",
        "description": "",
        "source": "",
        "tags": obj.get("tags", [])
    }
    materials.append(material)

# Build new inventory structure
new_data = {
    "materials": materials,
    "total_waste_mm": 0,
    "total_utilization_percent": 0.0,
    "cutting_sessions": [],
    "last_updated": datetime.now().isoformat(),
    "metadata": {
        "project": "bridge_design",
        "version": "2.0",
        "units": "millimeters"
    }
}

# Save to your agent's inventory file
with open("src/bridge_design_system/data/material_inventory.json", "w") as f:
    json.dump(new_data, f, indent=2)

print("Import complete! Your material_inventory.json is now updated.") 