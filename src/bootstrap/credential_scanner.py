import os
from dotenv import load_dotenv

def scan_credentials() -> dict:
    # Load environment variables
    load_dotenv()
    
    credentials = {}
    
    # Check for platform-specific tokens
    if os.getenv("NETLIFY_AUTH_TOKEN"):
        credentials["netlify"] = os.getenv("NETLIFY_AUTH_TOKEN")
    
    if os.getenv("VERCEL_TOKEN"):
        credentials["vercel"] = os.getenv("VERCEL_TOKEN")
    
    if os.getenv("GITHUB_TOKEN"):
        credentials["github"] = os.getenv("GITHUB_TOKEN")
    
    # Check local config files
    netlify_config_path = os.path.expanduser("~/.netlify/config.json")
    if os.path.exists(netlify_config_path):
        try:
            with open(netlify_config_path, 'r') as f:
                import json
                config = json.load(f)
                if "auth" in config:
                    credentials["netlify"] = config["auth"]
        except Exception:
            pass
    
    return credentials
