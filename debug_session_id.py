"""Debug session ID extraction from MCP server."""
import httpx

def debug_session_id():
    """Debug how MCP server handles session IDs."""
    
    print("🔍 Debugging MCP Session ID Handling")
    print("="*50)
    
    url = "http://localhost:8001/mcp/"
    
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "debug-client",
                "version": "1.0.0"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    print(f"📤 Sending initialization to: {url}")
    print(f"📤 Payload: {init_payload}")
    print(f"📤 Headers: {headers}")
    
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.post(url, json=init_payload, headers=headers)
            
            print(f"\n📥 Response Status: {response.status_code}")
            print(f"📥 Response Headers:")
            for key, value in response.headers.items():
                print(f"   {key}: {value}")
            
            print(f"\n📥 Response Text:")
            print(response.text)
            
            # Look for session info in different places
            session_id_locations = [
                ("Header X-Session-ID", response.headers.get("X-Session-ID")),
                ("Header Session-ID", response.headers.get("Session-ID")),
                ("Header Set-Cookie", response.headers.get("Set-Cookie")),
                ("Header Authorization", response.headers.get("Authorization")),
                ("Response text contains session", "session" in response.text.lower()),
            ]
            
            print(f"\n🔍 Session ID Search:")
            for location, value in session_id_locations:
                print(f"   {location}: {value}")
                
            # Parse SSE response
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    import json
                    try:
                        data = json.loads(line[6:])
                        print(f"\n📊 Parsed SSE Data: {data}")
                        if "result" in data:
                            print(f"📊 Result contains: {data['result']}")
                    except:
                        print(f"📊 Could not parse SSE data: {line}")
                        
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_session_id()