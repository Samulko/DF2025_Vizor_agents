# File: src/bridge_design_system/agents/category_smolagent.py
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any
import os
import logging

import google.generativeai as genai

from smolagents import CodeAgent, tool
from bridge_design_system.config.model_config import ModelProvider
from bridge_design_system.config.settings import settings

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Default data directory
BASE_DIR = Path(__file__).resolve().parents[1] / "data"

# ─── TOOLS ────────────────────────────────────────────────────────────────

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

@tool
def generate_tags_from_description(description: str) -> dict:
    """
    Clean up the description and generate tags using Google Generative AI.
    
    Args:
        description: Description of the physical object
        
    Returns:
        Dictionary with 'clean_description' (string) and 'tags' (list) keys.
        Example: {"clean_description": ..., "tags": [...]}
    """
    try:
        # Get Gemini API key from settings
        api_key = settings.gemini_api_key
        
        if not api_key:
            logger.error("Gemini API key not found in settings")
            return {"clean_description": description, "tags": []}
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Create the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare the prompt
        prompt = f"""
        For the following description of a physical object, provide:
        1. A clean, grammatically correct version of the description
        2. 2-5 concise, meaningful tags
        
        Format your response exactly like this:
        Clean Description: [clean description here]
        Tags: [tag1, tag2, tag3]
        
        Original description: '{description}'
        """
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Parse the response
        response_text = response.text.strip()
        
        # Extract clean description and tags
        clean_description = description  # fallback
        tags = []
        
        # Parse the structured response
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Clean Description:'):
                clean_description = line.replace('Clean Description:', '').strip()
            elif line.startswith('Tags:'):
                tags_part = line.replace('Tags:', '').strip()
                # Parse comma-separated tags
                tags = [tag.strip() for tag in tags_part.split(',') if tag.strip()]
        
        return {
            "clean_description": clean_description,
            "tags": tags
        }
        
    except Exception as e:
        logger.error(f"Tag generation failed: {e}")
        return {"clean_description": description, "tags": []}

# ─── AGENT FACTORY ────────────────────────────────────────────────────────

def create_category_agent(model_name: str = None) -> CodeAgent:
    agent_name = 'category'
    if model_name is None:
        model_name = getattr(settings, 'category_agent_model', 'gemini-2.5-flash-preview-05-20')
    model = ModelProvider.get_model(agent_name, temperature=None)
    # Register all computation tools, including tag generation
    tools = [calculate_distance, calculate_angles, save_categorized_data, generate_tags_from_description]
    agent = CodeAgent(
        tools=tools,
        model=model,
        max_steps=10,
        additional_authorized_imports=["math", "json", "pathlib", "typing"],
        name="category_agent",
        description="Classifies geometry shapes and manages material categories",
    )
    return agent

# ─── SHAPE ANALYSIS ───────────────────────────────────────────────────────

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

def generate_shape_description(shape_type, vertices, angles=None, side_lengths=None, perimeter=None):
    desc = f"A {shape_type} with vertices at {vertices}."
    if angles:
        desc += f" It has angles {', '.join(f'{a:.2f} degrees' for a in angles)}."
    if side_lengths:
        desc += f" The side lengths are {', '.join(f'{l:.4f}' for l in side_lengths)}."
    if perimeter:
        desc += f" Its perimeter is {perimeter:.4f}."
    return desc


# ─── MAIN PROCESSING LOGIC ────────────────────────────────────────────────

def process_catalog(catalog: Dict[str, Any], agent: CodeAgent) -> Dict[str, Any]:
    logger.info("Processing catalog items...")
    for obj in catalog.get("catalog", []):
        vertices = obj.get("vertices", [])
        raw_description = obj.get("description", "")
        # Clean up the description using the LLM
        cleaned_description = clean_description_with_llm(agent, raw_description)
        obj["description"] = cleaned_description
        # Generate tags from the cleaned description
        obj["tags"] = safe_generate_tags(agent, cleaned_description)
        # Analyze shape
        shape = analyze_shape(vertices)
        obj["shape_type"] = shape
        # Calculate angles, side lengths, perimeter
        angles = calculate_angles(vertices)
        side_lengths = [calculate_distance(vertices[i], vertices[(i+1)%len(vertices)]) for i in range(len(vertices))] if len(vertices) >= 3 else []
        perimeter = sum(side_lengths) if side_lengths else 0.0
        # Generate shape description (local, not LLM)
        desc = generate_shape_description(shape, vertices, angles, side_lengths, perimeter)
        obj["shape_analysis"] = desc
        obj["angles"] = angles
        obj["side_lengths"] = side_lengths
        obj["perimeter"] = perimeter
    logger.info("Catalog processing complete.")
    return catalog

# ─── CLI ENTRY POINT ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=BASE_DIR/"found_material_catalog.json")
    parser.add_argument("--output", type=str, default="material_categories.json")
    args = parser.parse_args()

    logger.info("Loading catalog...")
    catalog = load_catalog(args.catalog)
    logger.info("Creating category agent...")
    agent = create_category_agent()
    logger.info("Processing catalog...")
    updated_catalog = process_catalog(catalog, agent)
    logger.info("Saving updated catalog...")
    msg = save_categorized_data(updated_catalog, args.output)
    logger.info(msg)
    logger.info("Done.")

def testTags():
    description = "Eh, the first piece is 10 cm thick, no, 10 mm thick, wooden, and stiff"
    result = generate_tags_from_description(description)
    print("Result:", result)
    print("Clean Description:", result["clean_description"])
    print("Tags:", result["tags"])

def demo_category_agent():
    """
    Demonstrates how to create and use the category agent with a natural language task.
    """
    # Path of the json output in the data directory
    data_dir = Path(__file__).resolve().parents[1] / "data"
    jsonPath = data_dir / "demo_output.json"
    jsonPath = "demo_output.json"
    print("🤖 Creating category agent...")
    agent = create_category_agent()
    print(f"Agent created: {agent.name}")
    print(f"Available tools: {len(agent.tools)}")
    print(f"Max steps: {agent.max_steps}")

    # Example task for the agent
    print("\n📝 Running example agentic task...")

    # Use the jsonPath variable in the task string
    task = (
        f"Given the vertices [[0,0], [1,0], [1,1], [0,1]] and the description 'Eh, the first piece is 10 cm thick, no, 10 mm thick, wooden, and stiff', "
        f"classify the shape, calculate its angles and side lengths, generate a clean description and tags, and save the result to {jsonPath}."
    )
    result = agent.run(task)
    print(f"Result: {result}")

    # Check if json is created and throw an error if it's not
    if not jsonPath.exists():
        raise FileNotFoundError(f"❌ Output file '{jsonPath}' was not created by the agent.")
    else:
        print(f"✅ Output file '{jsonPath}' was successfully created.")


if __name__ == "__main__":
    # main()
    # testTags()
    demo_category_agent()
