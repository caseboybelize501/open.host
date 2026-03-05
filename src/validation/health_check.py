import requests

def check_health(url: str) -> bool:
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False
