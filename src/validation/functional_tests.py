import requests

def run_functional_tests(url: str, project_type: str) -> bool:
    # This is a simplified test - in practice this would be more complex
    try:
        response = requests.get(url, timeout=10)
        
        if project_type == "static":
            return response.status_code == 200 and "html" in response.headers.get("content-type", "")
        elif project_type == "node":
            # For Node.js apps, check for JSON API endpoints
            api_response = requests.get(f"{url}/api/status", timeout=10)
            return api_response.status_code == 200
        else:
            return response.status_code == 200
    except Exception:
        return False
