"""Debug MCP server connection issues."""
import httpx
import json

def debug_mcp_server():
    """Debug what's happening with the MCP server connection."""
    
    print("🔍 Debugging MCP Server Connection")
    print("="*50)
    
    base_url = "http://localhost:8001"
    
    # Test 1: Check if server is running
    print("📍 Test 1: Check if server is running")
    try:
        with httpx.Client() as client:
            response = client.get(f"{base_url}/grasshopper/status")
            print(f"✅ Server status: {response.status_code}")
            print(f"📊 Status response: {response.json()}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    # Test 2: Try GET on /mcp endpoint
    print(f"\n📍 Test 2: GET {base_url}/mcp")
    try:
        with httpx.Client() as client:
            response = client.get(f"{base_url}/mcp")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            if response.status_code in [307, 308]:
                print(f"🔄 Redirect location: {response.headers.get('location', 'No location header')}")
            print(f"Response text: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ GET /mcp failed: {e}")
    
    # Test 3: Try POST on /mcp endpoint with different headers
    print(f"\n📍 Test 3: POST {base_url}/mcp with JSON")
    try:
        payload = {
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
        
        with httpx.Client(follow_redirects=False) as client:
            response = client.post(
                f"{base_url}/mcp",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            if response.status_code in [307, 308]:
                print(f"🔄 Redirect location: {response.headers.get('location', 'No location header')}")
            print(f"Response text: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ POST /mcp failed: {e}")
    
    # Test 4: Try following redirects
    print(f"\n📍 Test 4: POST {base_url}/mcp with redirect following")
    try:
        with httpx.Client(follow_redirects=True) as client:
            response = client.post(
                f"{base_url}/mcp",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            print(f"Final status: {response.status_code}")
            print(f"Final URL: {response.url}")
            print(f"Response text: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ POST /mcp with redirects failed: {e}")
    
    # Test 5: Check what endpoints are actually available
    print(f"\n📍 Test 5: Try different endpoints")
    endpoints_to_test = [
        "/",
        "/mcp/",
        "/mcp/initialize", 
        "/mcp/tools/call",
        "/streamable-http",
        "/api",
    ]
    
    for endpoint in endpoints_to_test:
        try:
            with httpx.Client() as client:
                response = client.get(f"{base_url}{endpoint}")
                print(f"{endpoint}: {response.status_code}")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

if __name__ == "__main__":
    debug_mcp_server()