import httpx
from typing import Dict, List


def run_functional_tests(url: str, project_type: str) -> bool:
    """
    Run functional smoke tests based on project type.
    
    Args:
        url: URL of deployed application
        project_type: Type of project (react, vue, python, static, etc.)
    
    Returns:
        True if all tests pass
    """
    if not url:
        return False
    
    # Ensure URL has protocol
    if not url.startswith("http"):
        url = f"https://{url}"
    
    # Get tests for project type
    tests = _get_tests_for_project_type(project_type)
    
    # Run all tests
    all_passed = True
    for test in tests:
        if not test(url):
            all_passed = False
    
    return all_passed


def _get_tests_for_project_type(project_type: str) -> List:
    """Get list of test functions for project type."""
    common_tests = [
        _test_root_loads,
        _test_no_server_errors,
    ]
    
    type_specific_tests = {
        "react": [_test_react_specific],
        "vue": [_test_vue_specific],
        "next": [_test_next_specific],
        "python": [_test_python_specific],
        "node": [_test_node_specific],
        "static": [],
    }
    
    tests = common_tests.copy()
    tests.extend(type_specific_tests.get(project_type, []))
    
    return tests


def _test_root_loads(url: str) -> bool:
    """Test that root URL loads successfully."""
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
        return response.status_code == 200
    except Exception:
        return False


def _test_no_server_errors(url: str) -> bool:
    """Test that there are no 5xx server errors."""
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
        return response.status_code < 500
    except Exception:
        return False


def _test_react_specific(url: str) -> bool:
    """Test React-specific functionality."""
    try:
        response = httpx.get(url, timeout=10)
        content = response.text
        
        # Check for React root element
        has_root = 'id="root"' in content or 'id="app"' in content
        
        # Check for React scripts
        has_react = 'react' in content.lower() or 'chunk' in content.lower()
        
        return has_root or has_react
        
    except Exception:
        return False


def _test_vue_specific(url: str) -> bool:
    """Test Vue-specific functionality."""
    try:
        response = httpx.get(url, timeout=10)
        content = response.text
        
        # Check for Vue app element
        has_app = 'id="app"' in content
        
        # Check for Vue scripts
        has_vue = 'vue' in content.lower()
        
        return has_app or has_vue
        
    except Exception:
        return False


def _test_next_specific(url: str) -> bool:
    """Test Next.js-specific functionality."""
    try:
        response = httpx.get(url, timeout=10)
        content = response.text
        
        # Check for Next.js specific elements
        has_next = '__next' in content or 'next/data' in content
        
        return has_next
        
    except Exception:
        return False


def _test_python_specific(url: str) -> bool:
    """Test Python backend functionality."""
    try:
        # Test that we get a valid response
        response = httpx.get(url, timeout=10)
        return response.status_code in [200, 301, 302]
    except Exception:
        return False


def _test_node_specific(url: str) -> bool:
    """Test Node.js backend functionality."""
    try:
        response = httpx.get(url, timeout=10)
        return response.status_code in [200, 301, 302]
    except Exception:
        return False


def run_api_tests(url: str, endpoints: List[str]) -> Dict:
    """
    Run API endpoint tests.
    
    Args:
        url: Base URL
        endpoints: List of endpoint paths to test
    
    Returns:
        Dict with test results per endpoint
    """
    results = {}
    
    for endpoint in endpoints:
        test_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = httpx.get(test_url, timeout=10)
            results[endpoint] = {
                "status_code": response.status_code,
                "passed": response.status_code < 500,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            results[endpoint] = {
                "passed": False,
                "error": str(e)
            }
    
    return results


def run_browser_tests(url: str) -> Dict:
    """
    Run browser-based tests (placeholder for Playwright/Selenium).
    
    In a full implementation, this would:
    - Open page in headless browser
    - Check for JavaScript errors
    - Verify interactive elements work
    - Test navigation
    
    For now, returns basic HTTP checks.
    """
    results = {
        "page_loads": False,
        "no_js_errors": True,  # Would need browser to verify
        "interactive_works": False,  # Would need browser to verify
    }
    
    try:
        response = httpx.get(url, timeout=10)
        results["page_loads"] = response.status_code == 200
    except Exception:
        pass
    
    return results
