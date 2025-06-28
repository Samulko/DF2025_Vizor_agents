#!/usr/bin/env python
"""
Script to send a single message to the /HOLO1_GazePoint ROS topic.
Usage: python send_gaze.py <element_id>
Example: python send_gaze.py 020
"""

import sys
import time
import argparse
import roslibpy


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Send a gaze point message to ROS.")
    parser.add_argument("element_id", type=str, help="Element ID (e.g., 001, 020, 123)")
    parser.add_argument(
        "--host", type=str, default="localhost", help="ROS bridge server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=9090, help="ROS bridge server port (default: 9090)"
    )
    return parser.parse_args()


def send_gaze_point(element_id, host="localhost", port=9090):
    """
    Send a message to the /HOLO1_GazePoint topic with the element ID.

    Args:
        element_id: Element ID string (e.g., '020')
        host: ROS bridge host
        port: ROS bridge port
    """
    # Format the element ID as "dynamic_XXXX"
    message_data = f"dynamic_{element_id.zfill(3)}"

    try:
        # Connect to ROS bridge
        client = roslibpy.Ros(host=host, port=port)
        client.run()

        # Check if connected
        if not client.is_connected:
            print(f"Failed to connect to ROS bridge at {host}:{port}")
            return False

        print(f"Connected to ROS bridge at {host}:{port}")

        # Create publisher for the topic
        topic = roslibpy.Topic(client, "/HOLO1_GazePoint", "std_msgs/String")

        # Create and send the message
        message = {"data": message_data}
        print(f"Sending message: {message}")
        topic.publish(roslibpy.Message(message))

        # Small delay to ensure the message is sent
        time.sleep(0.5)

        # Clean up
        topic.unadvertise()
        client.terminate()

        print("Message sent successfully")
        return True

    except Exception as e:
        print(f"Error sending message: {e}")
        return False


if __name__ == "__main__":
    args = parse_arguments()
    success = send_gaze_point(args.element_id, args.host, args.port)
    sys.exit(0 if success else 1)
