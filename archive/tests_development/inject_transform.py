#!/usr/bin/env python3
"""
Script to inject transform data into a running main.py VizorListener instance.

This script simulates the HoloLens sending transform data by directly 
accessing the VizorListener singleton and adding data to its queue.

Usage:
1. Start main.py in interactive mode: `uv run python -m bridge_design_system.main --interactive`
2. Run this script: `python inject_transform.py [t1|t2]`
3. Watch the queue processing in main.py and element updates in Grasshopper

Example: python inject_transform.py t1
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Transform data from the original send_transform.py (converted to ROS→Rhino format)
TRANSFORM_T1_DATA = {
    "dynamic_001": {
        "position": [0.0, -0.0, 0.0],  # ROS→Rhino: [-y, x, z]
        "quaternion": [-1.0, 0.0, -0.0, 0.0]  # ROS→Rhino: [w, -y, x, z]
    },
    "dynamic_002": {
        "position": [0.08316001296043396, -0.06644491851329803, 0.33045026659965515],
        "quaternion": [-1.0, -0.0, 0.0, -0.0]
    },
    "dynamic_003": {
        "position": [-0.06487333029508591, -0.3439379036426544, -0.025135979056358337],
        "quaternion": [-1.0, -0.0, 0.0, -0.0]
    }
}

TRANSFORM_T2_DATA = {
    "dynamic_001": {
        "position": [0.0, -0.0, 0.0],
        "quaternion": [-1.0, 0.0, -0.0, 0.0]
    },
    "dynamic_002": {
        "position": [0.18176478147506714, -0.2936401963233948, -0.044508472084999084],
        "quaternion": [-1.0, -0.0, 0.0, -0.0]
    },
    "dynamic_003": {
        "position": [0.12241509556770325, -0.30347174406051636, -0.15938685834407806],
        "quaternion": [-1.0, -0.0, 0.0, -0.0]
    }
}

def inject_transform_data(transform_type="t1"):
    """
    Inject transform data into the running VizorListener instance.
    
    Args:
        transform_type: "t1" or "t2" for different transform configurations
    """
    print(f"🧪 Transform Injection Test - {transform_type.upper()}")
    print("=" * 50)
    
    try:
        # Import VizorListener to access the singleton instance
        from src.bridge_design_system.agents.VizorListener import VizorListener
        
        print("🔍 Accessing running VizorListener instance...")
        
        # Get the singleton instance (should be created by main.py)
        vizor_listener = VizorListener()
        
        # Check if it has an update_queue (set by main.py)
        if not hasattr(vizor_listener, 'update_queue'):
            print("❌ VizorListener instance doesn't have update_queue")
            print("💡 Make sure main.py is running in interactive mode first!")
            return False
            
        if vizor_listener.update_queue is None:
            print("❌ VizorListener update_queue is None")
            print("💡 Make sure main.py is running in interactive mode first!")
            return False
        
        print(f"✅ VizorListener found with queue (current size: {len(vizor_listener.update_queue)})")
        
        # Select transform data
        transform_data = TRANSFORM_T1_DATA if transform_type == "t1" else TRANSFORM_T2_DATA
        
        print(f"📡 Injecting {transform_type.upper()} transform data...")
        print(f"Elements: {list(transform_data.keys())}")
        
        # Inject the transform data directly into the queue
        # This simulates what _handle_model_message would do
        vizor_listener.update_queue.append(transform_data.copy())
        
        print(f"✅ Transform data injected! Queue size: {len(vizor_listener.update_queue)}")
        print()
        print("🎯 Next steps:")
        print("1. Switch to your main.py terminal")
        print("2. Press ENTER or type any command")
        print("3. Watch the queue processing and element updates")
        print("4. Check Rhino Grasshopper to see if elements moved")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the project directory and main.py dependencies are available")
        return False
    except Exception as e:
        print(f"❌ Injection failed: {e}")
        print("💡 Make sure main.py is running in interactive mode in another terminal")
        return False

def main():
    """Main entry point for the injection script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Inject transform data into running main.py')
    parser.add_argument('transform_type', nargs='?', default='t1', choices=['t1', 't2'],
                        help='Transform type to inject (t1 or t2, default: t1)')
    
    args = parser.parse_args()
    
    print("🧪 Transform Data Injection Tool")
    print("This injects transform data into a running main.py instance")
    print()
    print("Prerequisites:")
    print("1. main.py must be running: uv run python -m bridge_design_system.main --interactive")
    print("2. Rhino Grasshopper should be open with bridge components")
    print("3. MCP server should be running if needed")
    print()
    
    success = inject_transform_data(args.transform_type)
    
    if success:
        print("\n✅ Transform data injection completed!")
        print("👀 Check your main.py terminal for queue processing")
    else:
        print("\n❌ Transform data injection failed!")
        print("💡 Make sure main.py is running in interactive mode first")
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()