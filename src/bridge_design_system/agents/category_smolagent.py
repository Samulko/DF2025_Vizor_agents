# File: src/bridge_design_system/agents/category_smolagent.py
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any

from smolagents import CodeAgent, tool
from bridge_design_system.config.logging_config import get_logger
from bridge_design_system.config.model_config import ModelProvider
from bridge_design_system.config.settings import settings


logger = get_logger(__name__)

# 默认数据目录
# category_smolagent.py
BASE_DIR = Path(__file__).resolve().parents[1] / "data"



# ─── STEP 1: TOOLS ────────────────────────────────────────────────────────────

@tool
def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    Compute the Euclidean distance between two 2D points.

    Args:
        point1: Coordinates of the first point as [x, y].
        point2: Coordinates of the second point as [x, y].

    Returns:
        The Euclidean distance between point1 and point2.
    """
    return math.hypot(point2[0] - point1[0], point2[1] - point1[1])


@tool
def calculate_angles(vertices: List[List[float]]) -> List[float]:
    """
    Calculate the angles between consecutive edges in a 2D polygon.

    Args:
        vertices: List of vertex coordinates [[x1, y1], [x2, y2], ...].

    Returns:
        List of angles (in degrees) between each pair of consecutive edges.
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
            cos_a = max(-1.0, min(1.0, (v1[0]*v2[0] + v1[1]*v2[1])/(mag1*mag2)))
            angles.append(math.degrees(math.acos(cos_a)))
        else:
            angles.append(0.0)
    return angles


@tool
def save_categorized_data(data: Dict[str, Any], filename: str) -> str:
    """
    Save categorized material data to a JSON file, ensuring directory exists.

    Args:
        data: The categorized material data to write out.
        filename: Name of the output JSON file.

    Returns:
        A string message indicating where the data was saved.
    """
    out_path = BASE_DIR / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return f"✅ Data written to {out_path}"


# ─── STEP 2: AGENT FACTORY ────────────────────────────────────────────────────

def create_category_agent(model_name: str = None) -> CodeAgent:
    """
    Create a category agent for shape analysis.
    """
    agent_name = 'category'
    if model_name is None:
        model_name = getattr(settings, 'category_agent_model', 'gemini-2.5-flash-preview-05-20')
    model = ModelProvider.get_model(agent_name, temperature=None)
    tools = [calculate_distance, calculate_angles, save_categorized_data]
    agent = CodeAgent(
        tools=tools,
        model=model,
        max_steps=10,
        additional_authorized_imports=["math", "json", "pathlib", "typing"],
        name="category_agent",
        description="Classifies geometry shapes and manages material categories",
    )
    return agent


# ─── STEP 3: SHAPE ANALYSIS ──────────────────────────────────────────────────

def load_catalog(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_shape(vertices: List[List[float]]) -> str:
    """
    Analyze and classify a shape based on its vertices.

    Args:
        vertices: List of vertex coordinates [[x1, y1], [x2, y2], ...].

    Returns:
        The shape type as a string (e.g., 'triangle', 'square', 'hexagon', 'octagon', 'polygon_N').
    """
    n = len(vertices)
    if n == 3:
        return "triangle"
    elif n == 4:
        # Check if it's a square (all sides equal, all angles ~90)
        sides = [calculate_distance(vertices[i], vertices[(i+1)%4]) for i in range(4)]
        angles = calculate_angles(vertices)
        if len(set(round(s, 3) for s in sides)) == 1 and all(abs(a - 90) < 5 for a in angles):
            return "square"
        else:
            return "quadrilateral"
    elif n == 6:
        return "hexagon"
    elif n == 8:
        return "octagon"
    elif n > 8:
        return f"polygon_{n}"
    else:
        return f"polygon_{n}"


def categorize(catalog: Dict[str, Any]) -> Dict[str, Any]:
    """
    Categorize shapes into triangles, squares, hexagons, octagons, and general polygons.
    Polygons with 8 or more sides are grouped as 'polygon_8plus'.
    """
    stats = {"total": 0, "types": {}}
    categorized = {
        "triangle": [],
        "square": [],
        "hexagon": [],
        "octagon": [],
        "polygon_8plus": [],
        "other_polygons": []
    }
    for obj in catalog.get("catalog", []):
        stats["total"] += 1
        verts = obj.get("vertices", [])
        shape = analyze_shape(verts)
        if shape == "triangle":
            categorized["triangle"].append(obj)
            stats["types"]["triangle"] = stats["types"].get("triangle", 0) + 1
        elif shape == "square":
            categorized["square"].append(obj)
            stats["types"]["square"] = stats["types"].get("square", 0) + 1
        elif shape == "hexagon":
            categorized["hexagon"].append(obj)
            stats["types"]["hexagon"] = stats["types"].get("hexagon", 0) + 1
        elif shape == "octagon":
            categorized["octagon"].append(obj)
            stats["types"]["octagon"] = stats["types"].get("octagon", 0) + 1
        elif shape.startswith("polygon_"):
            n = int(shape.split("_")[1])
            if n >= 8:
                categorized["polygon_8plus"].append(obj)
                stats["types"]["polygon_8plus"] = stats["types"].get("polygon_8plus", 0) + 1
            else:
                categorized["other_polygons"].append(obj)
                stats["types"]["other_polygons"] = stats["types"].get("other_polygons", 0) + 1
        else:
            categorized["other_polygons"].append(obj)
            stats["types"]["other_polygons"] = stats["types"].get("other_polygons", 0) + 1
    categorized["stats"] = stats
    return categorized


# ─── STEP 4: DEMO & CLI ────────────────────────────────────────────────────────

def demo(catalog_file: Path, out_file: str):
    logger.info("Loading catalog...")
    catalog = load_catalog(catalog_file)
    agent = create_category_agent()
    logger.info("Categorizing locally...")
    result = categorize(catalog)
    logger.info(f"Total objects: {result['stats']['total']}")
    # Save each category to its own file
    for shape in ["triangle", "square", "hexagon", "octagon", "polygon_8plus", "other_polygons"]:
        if result[shape]:
            fname = f"{shape}_categories.json"
            msg = save_categorized_data(result[shape], fname)
            logger.info(f"{shape.capitalize()}s: {msg}")
    # Save a general file with all categories
    general_categories = {shape: result[shape] for shape in ["triangle", "square", "hexagon", "octagon", "polygon_8plus", "other_polygons"]}
    msg = save_categorized_data(general_categories, "all_categories.json")
    logger.info(f"All categories: {msg}")
    # Optionally, run analysis for each shape type
    for shape in ["triangle", "square", "hexagon", "octagon", "polygon_8plus", "other_polygons"]:
        sample = result[shape][:3] if result[shape] else []
        if sample:
            prompt = (
                f"The variable `{shape}` is a list of objects to analyze.\n"
                f"{shape} = {sample}\n"
                f"Please analyze the list `{shape}`."
            )
            analysis = agent.run(prompt)
            if isinstance(analysis, (dict, list)):
                analysis_str = json.dumps(analysis, ensure_ascii=False, indent=2)
            else:
                analysis_str = str(analysis)
            logger.info(f"Agent analysis for {shape}s:\n{analysis_str}")



if __name__=="__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", type=Path, default=BASE_DIR/"found_material_catalog.json")
    p.add_argument("--output", type=str, default="material_categories.json")
    args = p.parse_args()
    demo(args.catalog, args.output)
