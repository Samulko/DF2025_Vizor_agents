# File: src/bridge_design_system/agents/category_smolagent.py
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any

from smolagents import CodeAgent, tool
from src.bridge_design_system.config.logging_config import get_logger
from src.bridge_design_system.config.model_config import ModelProvider

logger = get_logger(__name__)

# 默认数据目录
# category_smolagent.py
BASE_DIR = Path(__file__).resolve().parents[1] / "data"



# ─── STEP 1: TOOLS ────────────────────────────────────────────────────────────

from smolagents import tool
from typing import List
import math

@tool
def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    Calculate the Euclidean distance between two 2D points.

    Args:
        point1: The x and y coordinates of the first point as a list of two floats.
        point2: The x and y coordinates of the second point as a list of two floats.

    Returns:
        The Euclidean distance between the two points.
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)




@tool
def calculate_angles(vertices: List[List[float]]) -> List[float]:
    """
    Calculate the angles between consecutive edges in a polygon.

    Args:
        vertices: A list of points, each a list of two floats [x, y], representing the polygon's vertices.

    Returns:
        A list of angles (in degrees) between each pair of consecutive edges.
    """
    if len(vertices) < 3:
        return []
    angles = []
    n = len(vertices)
    for i in range(n):
        prev, curr, nxt = vertices[i], vertices[(i+1)%n], vertices[(i+2)%n]
        v1 = (curr[0] - prev[0], curr[1] - prev[1])
        v2 = (nxt[0] - curr[0], nxt[1] - curr[1])
        mag1, mag2 = math.hypot(*v1), math.hypot(*v2)
        if mag1 and mag2:
            cos_a = max(-1.0, min(1.0, (v1[0]*v2[0]+v1[1]*v2[1])/(mag1*mag2)))
            angles.append(math.degrees(math.acos(cos_a)))
        else:
            angles.append(0.0)
    return angles

@tool
def save_categorized_data(data: Dict[str, Any], filename: str) -> str:
    """
    Save categorized material data to a JSON file.

    Args:
        data: The categorized data to save.
        filename: The name of the output JSON file.

    Returns:
        A string message indicating where the data was saved.
    """
    out_path = BASE_DIR / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return f"Data written to {out_path}"

@tool
def generate_tags_from_description(description: str) -> list:
    """
    Generate prompt tags from a description.

    Args:
        description: The descriptive text for the object.

    Returns:
        A list of tags extracted from the description.
    """
    # Simple placeholder: split by spaces, remove punctuation
    import re
    words = re.findall(r'\b\w+\b', description.lower())
    return list(set(words))

# ─── STEP 2: AGENT FACTORY ────────────────────────────────────────────────────

def create_material_agent(model_name: str = "default") -> CodeAgent:
    model = ModelProvider.get_model(model_name)
    tools = [calculate_distance, calculate_angles, save_categorized_data]
    agent = CodeAgent(
        tools=tools,
        model=model,
        max_steps=10,
        additional_authorized_imports=["math", "json", "pathlib", "typing"],
        name="category_material_agent",
        description="Classifies geometry shapes and manages material categories",
    )
    return agent


# ─── STEP 3: SHAPE ANALYSIS ──────────────────────────────────────────────────

def load_catalog(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_triangle_shape(verts: List[List[float]]) -> str:
    if len(verts) != 3:
        return "invalid_triangle"
    sides = [calculate_distance(verts[i], verts[(i+1)%3]) for i in range(3)]
    angles = calculate_angles(verts)
    if any(a > 90 for a in angles):
        return "obtuse_triangle"
    if any(abs(a-90)<1 for a in angles):
        return "right_triangle"
    uniq = len(set(round(s,3) for s in sides))
    return {1:"equilateral_triangle",2:"isosceles_triangle"}.get(uniq, "scalene_triangle")

def categorize(catalog: Dict[str, Any], agent=None) -> Dict[str, Any]:
    stats = {"total":0, "triangles":0, "types":{}}
    tris, others = [], []
    for obj in catalog.get("catalog",[]):
        stats["total"] += 1
        verts = obj.get("vertices",[])
        description = obj.get("description", "")
        tags = []
        if description:
            # Use the tool directly if agent is None, else use agent to run the tool
            if agent:
                tags = agent.run(f"generate_tags_from_description(description='{description}')")
                # Try to parse tags as a list if returned as string
                if isinstance(tags, str):
                    import ast
                    try:
                        tags = ast.literal_eval(tags)
                    except Exception:
                        tags = [tags]
            else:
                tags = generate_tags_from_description(description)
        if len(verts)==3:
            t = analyze_triangle_shape(verts)
            tris.append({"id":obj["id"],"type":t, "description": description, "tags": tags})
            stats["triangles"] += 1
            stats["types"][t] = stats["types"].get(t,0) + 1
        else:
            others.append({"id":obj["id"],"verts":len(verts), "description": description, "tags": tags})
    return {"triangles":tris, "others":others, "stats":stats}


# ─── STEP 4: DEMO & CLI ────────────────────────────────────────────────────────

def demo(catalog_file: Path, out_file: str, model_name: str = "material"):
    logger.info("Loading catalog...")
    catalog = load_catalog(catalog_file)
    agent = create_material_agent(model_name)
    logger.info("Categorizing locally...")
    result = categorize(catalog, agent)
    logger.info(f"Found {result['stats']['triangles']} triangles out of {result['stats']['total']}")
    # 1) 保存
    msg = agent.run(f"save_categorized_data(data={result}, filename='{out_file}')")
    logger.info(msg)
    # 2) 详细分析示例（三角形前三个）
    sample = result["triangles"][:3]
    prompt = f"Please analyze these triangles: {sample}"
    analysis = agent.run(prompt)
    logger.info("Agent analysis:\n" + analysis)

# Aliases for compatibility with imports in __init__.py and main.py
create_category_material_agent = create_material_agent
demo_level_checking = demo

if __name__=="__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", type=Path, default=Path("/mnt/c/Users/zzyal/Documents/GitHub/DF2025_Vizor_agents/import_found_materials.py"))
    p.add_argument("--output", type=str, default="material_categories.json")
    p.add_argument("--model_name", type=str, default="material", help="Agent name for model selection (e.g., material, triage, geometry, etc.)")
    args = p.parse_args()
    demo(args.catalog, args.output, args.model_name)
