import pytest

try:
    from .model_config import test_model_api_connectivity
    import requests
except ImportError:
    test_model_api_connectivity = None

from .settings import settings

@pytest.mark.skipif(test_model_api_connectivity is None, reason="requests or model_config not available")
def test_api_connectivity():
    results = test_model_api_connectivity()
    assert isinstance(results, dict)
    # At least one provider should be present
    assert len(results) > 0
    # All values should be boolean
    for v in results.values():
        assert isinstance(v, bool)
    print("Model API connectivity results:", results)

@pytest.mark.skipif('requests' not in globals(), reason="requests not available")
def test_grasshopper_connection():
    url = getattr(settings, 'mcp_grasshopper_url', 'http://localhost:8081')
    # Try /status endpoint if available, else root
    for endpoint in ["/status", "/", ""]:
        try:
            resp = requests.get(url.rstrip("/") + endpoint, timeout=5)
            print(f"Tried {url.rstrip('/') + endpoint}: status {resp.status_code}")
            # Accept any 2xx or 3xx as success
            if 200 <= resp.status_code < 400:
                return
        except Exception as e:
            print(f"Failed to connect to {url.rstrip('/') + endpoint}: {e}")
    pytest.fail(f"Could not connect to Grasshopper server at {url}") 