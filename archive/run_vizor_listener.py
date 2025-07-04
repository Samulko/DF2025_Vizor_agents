#!/usr/bin/env python3
"""
Standalone runner for VizorListener agent.

This script creates and runs a VizorListener instance to demonstrate
its functionality for listening to ROS topics and processing gaze/model data.
"""

import time
import signal
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_design_system.agents.VizorListener import VizorListener


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Received interrupt signal. Cleaning up...")
    if vizor_listener:
        vizor_listener.cleanup()
    print("✅ Cleanup completed. Exiting.")
    sys.exit(0)


def print_status(vizor_listener):
    """Print current status of the VizorListener."""
    print("\n" + "="*60)
    print("📊 VIZOR LISTENER STATUS")
    print("="*60)
    
    # Connection status
    status = vizor_listener.get_connection_status()
    print(f"🔗 ROS Available: {status['ros_available']}")
    print(f"🔗 Connection Attempted: {status['connection_attempted']}")
    print(f"🔗 Client Exists: {status['client_exists']}")
    print(f"🔗 Is Connected: {status['is_connected']}")
    print(f"👁️ Gaze Subscriber: {status['gaze_subscriber_active']}")
    print(f"🎯 Model Subscriber: {status['model_subscriber_active']}")
    
    # Current state
    print(f"\n🎯 Current Element: {vizor_listener.get_current_element()}")
    print(f"🔄 Recent Gaze: {vizor_listener.get_recent_gaze()}")
    
    # Gaze history summary
    summary = vizor_listener.get_gaze_history_summary()
    print(f"\n📈 Gaze History Summary (last 10s):")
    print(f"   Total Gazes: {summary['total_gazes']}")
    print(f"   Unique Elements: {summary['unique_elements']}")
    print(f"   Most Gazed: {summary['most_gazed']} ({summary['most_gazed_count']} times)")
    print(f"   Recent Elements: {summary['recent_elements']}")
    
    # Transforms
    transforms = vizor_listener.get_transforms()
    if transforms:
        print(f"\n🎯 Active Transforms ({len(transforms)}):")
        for name, transform in transforms.items():
            pos = transform.get('position', [0, 0, 0])
            quat = transform.get('quaternion', {'w': 1, 'x': 0, 'y': 0, 'z': 0})
            print(f"   {name}: pos={pos}, quat=({quat['w']:.3f}, {quat['x']:.3f}, {quat['y']:.3f}, {quat['z']:.3f})")
    else:
        print(f"\n🎯 Active Transforms: None")
    
    print("="*60)


def main():
    """Main function to run the VizorListener."""
    global vizor_listener
    
    print("🚀 Starting VizorListener Agent...")
    print("📡 This agent listens to ROS topics for gaze and model data")
    print("🔄 Press Ctrl+C to stop the agent")
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create update queue for transforms
    update_queue = []
    
    # Initialize VizorListener
    print("\n🔧 Initializing VizorListener...")
    vizor_listener = VizorListener(update_queue=update_queue)
    
    # Print initial status
    print_status(vizor_listener)
    
    # Main loop
    print("\n🔄 Entering main loop...")
    print("📡 Listening for ROS messages...")
    print("💡 The agent will automatically process incoming gaze and model data")
    
    last_status_time = time.time()
    status_interval = 5.0  # Print status every 5 seconds
    
    try:
        while True:
            current_time = time.time()
            
            # Print periodic status updates
            if current_time - last_status_time >= status_interval:
                print_status(vizor_listener)
                last_status_time = current_time
            
            # Check for updates in the queue
            if update_queue:
                print(f"\n📬 Processing {len(update_queue)} queued updates...")
                while update_queue:
                    transform_data = update_queue.pop(0)
                    print(f"   Processing transform data: {list(transform_data.keys())}")
            
            # Sleep briefly to avoid busy waiting
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    except Exception as e:
        print(f"\n❌ Error in main loop: {e}")
    finally:
        # Cleanup
        if vizor_listener:
            print("\n🧹 Cleaning up VizorListener...")
            vizor_listener.cleanup()
        print("✅ Cleanup completed")


if __name__ == "__main__":
    vizor_listener = None
    main() 