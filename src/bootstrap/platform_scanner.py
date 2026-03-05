import httpx
from typing import List, Dict

def scan_platforms() -> List[Dict]:
    platforms = [
        {
            "name": "netlify",
            "api_url": "https://api.netlify.com/api/v1",
            "free_tier": True,
            "supported_types": ["static", "node", "python"]
        },
        {
            "name": "vercel",
            "api_url": "https://api.vercel.com",
            "free_tier": True,
            "supported_types": ["static", "node", "python"]
        },
        {
            "name": "github_pages",
            "api_url": "https://api.github.com",
            "free_tier": True,
            "supported_types": ["static"]
        },
        {
            "name": "render",
            "api_url": "https://api.render.com",
            "free_tier": True,
            "supported_types": ["node", "python"]
        },
        {
            "name": "surge",
            "api_url": "https://surge.sh",
            "free_tier": True,
            "supported_types": ["static"]
        }
    ]
    
    # Validate platform availability
    available_platforms = []
    for platform in platforms:
        try:
            response = httpx.get(platform["api_url"], timeout=5)
            if response.status_code == 200:
                available_platforms.append(platform)
        except Exception:
            continue
    
    return available_platforms
