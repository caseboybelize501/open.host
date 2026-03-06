import httpx
from typing import List, Dict, Optional


def scan_platforms() -> List[Dict]:
    """
    Scan available hosting platforms and check their API health.
    
    Platforms scanned:
    - Netlify: Static/JAMstack hosting with functions
    - Vercel: Next.js platform with serverless/edge functions
    - GitHub Pages: Static site hosting
    - Render: Full-stack hosting with databases
    - Surge: Simple static site hosting
    
    Returns:
        List of available platforms with metadata
    """
    platforms = _get_platform_definitions()
    
    # Validate platform availability
    available_platforms = []
    for platform in platforms:
        health = _check_platform_health(platform)
        platform["healthy"] = health["healthy"]
        platform["response_time_ms"] = health.get("response_time_ms")
        
        # Include platform even if API check fails (might be temporary)
        available_platforms.append(platform)
    
    return available_platforms


def _get_platform_definitions() -> List[Dict]:
    """Get platform configuration definitions."""
    return [
        {
            "name": "netlify",
            "display_name": "Netlify",
            "api_url": "https://api.netlify.com/api/v1",
            "website": "https://netlify.com",
            "free_tier": True,
            "supported_types": ["static", "node", "react", "vue", "angular", "svelte", "gatsby", "nuxt"],
            "features": ["spa", "static", "cdn", "functions", "redirects", "forms"],
            "limits": {
                "bandwidth": "100GB/month",
                "build_minutes": "300/month",
                "sites": "unlimited"
            },
            "cli_tool": "netlify-cli",
            "env_var": "NETLIFY_AUTH_TOKEN"
        },
        {
            "name": "vercel",
            "display_name": "Vercel",
            "api_url": "https://api.vercel.com",
            "website": "https://vercel.com",
            "free_tier": True,
            "supported_types": ["static", "node", "react", "vue", "angular", "svelte", "next", "nuxt", "gatsby", "remix"],
            "features": ["spa", "static", "cdn", "serverless", "edge-functions", "preview-deployments"],
            "limits": {
                "bandwidth": "100GB/month",
                "build_minutes": "6000/month",
                "projects": "unlimited"
            },
            "cli_tool": "vercel",
            "env_var": "VERCEL_TOKEN"
        },
        {
            "name": "github_pages",
            "display_name": "GitHub Pages",
            "api_url": "https://api.github.com",
            "website": "https://pages.github.com",
            "free_tier": True,
            "supported_types": ["static"],
            "features": ["static", "cdn", "jekyll", "custom-domain"],
            "limits": {
                "bandwidth": "unlimited",
                "build_minutes": "N/A",
                "sites": "unlimited"
            },
            "cli_tool": "gh",
            "env_var": "GITHUB_TOKEN"
        },
        {
            "name": "render",
            "display_name": "Render",
            "api_url": "https://api.render.com",
            "website": "https://render.com",
            "free_tier": True,
            "supported_types": ["node", "python", "docker", "go", "rust", "static"],
            "features": ["server", "database", "docker", "cron", "background-workers"],
            "limits": {
                "bandwidth": "unlimited",
                "build_minutes": "N/A",
                "services": "limited (free tier)"
            },
            "cli_tool": "render",
            "env_var": "RENDER_API_KEY"
        },
        {
            "name": "surge",
            "display_name": "Surge",
            "api_url": "https://surge.sh",
            "website": "https://surge.sh",
            "free_tier": True,
            "supported_types": ["static"],
            "features": ["static", "cdn", "ssl", "custom-domain"],
            "limits": {
                "bandwidth": "unlimited",
                "build_minutes": "N/A",
                "sites": "unlimited"
            },
            "cli_tool": "surge",
            "env_var": "SURGE_TOKEN"
        }
    ]


def _check_platform_health(platform: Dict) -> Dict:
    """Check platform API health."""
    api_url = platform.get("api_url")
    
    if not api_url:
        return {"healthy": False, "error": "No API URL defined"}
    
    try:
        import time
        start = time.time()
        response = httpx.get(api_url, timeout=5, follow_redirects=True)
        response_time_ms = int((time.time() - start) * 1000)
        
        # Most APIs return 200 or 401/403 (auth required) when healthy
        healthy = response.status_code in [200, 401, 403, 404]
        
        return {
            "healthy": healthy,
            "status_code": response.status_code,
            "response_time_ms": response_time_ms
        }
        
    except httpx.TimeoutException:
        return {"healthy": False, "error": "Timeout"}
    except httpx.ConnectError:
        return {"healthy": False, "error": "Connection failed"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


def get_platform_by_name(name: str) -> Optional[Dict]:
    """Get platform definition by name."""
    platforms = _get_platform_definitions()
    for platform in platforms:
        if platform["name"] == name:
            return platform
    return None


def get_platforms_for_project_type(project_type: str) -> List[Dict]:
    """Get platforms that support a specific project type."""
    platforms = scan_platforms()
    return [
        p for p in platforms 
        if project_type in p.get("supported_types", [])
    ]


def get_platform_features(platform_name: str) -> List[str]:
    """Get features supported by a platform."""
    platform = get_platform_by_name(platform_name)
    return platform.get("features", []) if platform else []
