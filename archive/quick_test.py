#!/usr/bin/env python3
"""
Quick test to verify the transform flow
"""
import time
import threading
import roslibpy
import json

def listener_thread():
    """Run listener in separate thread"""
    print("📡 Starting listener thread...")
    
    client = roslibpy.Ros(host='localhost', port=9090)
    client.run()
    
    def handle_message(msg):
        print(f"\n✅ RECEIVED: {msg}")
    
    topic = roslibpy.Topic(client, '/HOLO1_Model', 'std_msgs/String')
    topic.subscribe(handle_message)
    
    print("👂 Listener ready...")
    time.sleep(10)  # Listen for 10 seconds
    
    topic.unsubscribe()
    client.terminate()
    print("📡 Listener stopped")

def sender_function():
    """Send a message after listener is ready"""
    time.sleep(2)  # Wait for listener to be ready
    
    print("📤 Sending message...")
    
    client = roslibpy.Ros(host='localhost', port=9090)
    client.run()
    
    topic = roslibpy.Topic(client, '/HOLO1_Model', 'std_msgs/String')
    
    message_data = {
        'names': ['dynamic_001', 'dynamic_002'],
        'poses': [
            {
                'position': {'x': 1.0, 'y': 2.0, 'z': 3.0},
                'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
            },
            {
                'position': {'x': 4.0, 'y': 5.0, 'z': 6.0},
                'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
            }
        ]
    }
    
    message = {'data': json.dumps(message_data)}
    topic.publish(roslibpy.Message(message))
    
    time.sleep(1)
    topic.unadvertise()
    client.terminate()
    print("📤 Message sent")

if __name__ == "__main__":
    print("🚀 Quick Test: Listener + Sender")
    
    # Start listener thread
    listener = threading.Thread(target=listener_thread)
    listener.start()
    
    # Start sender
    sender_function()
    
    # Wait for listener to finish
    listener.join()
    
    print("✅ Quick test complete")