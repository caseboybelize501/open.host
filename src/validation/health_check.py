import httpx
from typing import Dict


def check_health(url: str) -> bool:
    """
    Check if a URL is healthy (returns 200 OK).
    
    Args:
        url: URL to check
    
    Returns:
        True if healthy (200 OK), False otherwise
    """
    if not url:
        return False
    
    # Ensure URL has protocol
    if not url.startswith("http"):
        url = f"https://{url}"
    
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
        return response.status_code == 200
    except Exception:
        return False


def check_health_detailed(url: str) -> Dict:
    """
    Check health with detailed response information.
    
    Returns:
        Dict with status_code, response_time, and error (if any)
    """
    result = {
        "healthy": False,
        "status_code": None,
        "response_time_ms": None,
        "error": None
    }
    
    if not url:
        result["error"] = "No URL provided"
        return result
    
    if not url.startswith("http"):
        url = f"https://{url}"
    
    try:
        import time
        start = time.time()
        
        response = httpx.get(url, timeout=10, follow_redirects=True)
        
        result["status_code"] = response.status_code
        result["response_time_ms"] = int((time.time() - start) * 1000)
        result["healthy"] = response.status_code == 200
        
    except httpx.TimeoutException:
        result["error"] = "Request timed out"
    except httpx.ConnectError as e:
        result["error"] = f"Connection failed: {str(e)}"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def check_ssl(url: str) -> bool:
    """
    Check if URL uses HTTPS with valid certificate.
    
    Args:
        url: URL to check
    
    Returns:
        True if HTTPS with valid cert, False otherwise
    """
    if not url:
        return False
    
    # Must use HTTPS
    if not url.startswith("https://"):
        return False
    
    try:
        import ssl
        import socket
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port or 443
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Try to connect
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Check certificate
                cert = ssock.getpeercert()
                return cert is not None
                
    except Exception:
        return False


def check_endpoint(url: str, method: str = "GET", 
                   expected_status: int = 200) -> bool:
    """
    Check a specific endpoint with custom method.
    
    Args:
        url: URL to check
        method: HTTP method to use
        expected_status: Expected status code
    
    Returns:
        True if expected status received
    """
    if not url:
        return False
    
    if not url.startswith("http"):
        url = f"https://{url}"
    
    try:
        response = httpx.request(method, url, timeout=10, follow_redirects=True)
        return response.status_code == expected_status
    except Exception:
        return False
