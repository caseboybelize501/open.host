import os
import json
from typing import Dict, Optional
from pathlib import Path


def scan_credentials() -> Dict[str, str]:
    """
    Scan for hosting platform credentials from multiple sources.
    
    Sources checked (in order):
    1. Environment variables
    2. .env file in current directory
    3. Platform-specific config files (~/.netlify, ~/.vercel, etc.)
    4. OS keyring (if available)
    
    Returns:
        Dict mapping platform name to credential token
    """
    credentials = {}
    
    # 1. Check environment variables
    env_credentials = _scan_environment_variables()
    credentials.update(env_credentials)
    
    # 2. Check .env file
    dotenv_credentials = _scan_dotenv()
    credentials.update(dotenv_credentials)
    
    # 3. Check platform config files
    file_credentials = _scan_config_files()
    credentials.update(file_credentials)
    
    # 4. Try OS keyring (optional)
    try:
        keyring_credentials = _scan_keyring()
        credentials.update(keyring_credentials)
    except Exception:
        pass  # Keyring not available or failed
    
    return credentials


def _scan_environment_variables() -> Dict[str, str]:
    """Scan environment variables for credentials."""
    credentials = {}
    
    env_mappings = {
        "netlify": ["NETLIFY_AUTH_TOKEN", "NETLIFY_TOKEN"],
        "vercel": ["VERCEL_TOKEN", "NOW_TOKEN"],
        "github": ["GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT"],
        "render": ["RENDER_API_KEY", "RENDER_TOKEN"],
        "surge": ["SURGE_TOKEN"],
        "gitlab": ["GITLAB_TOKEN"],
        "aws": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    }
    
    for platform, env_vars in env_mappings.items():
        for env_var in env_vars:
            value = os.getenv(env_var)
            if value:
                credentials[platform] = value
                break  # Found credential for this platform
    
    return credentials


def _scan_dotenv() -> Dict[str, str]:
    """Scan .env file for credentials."""
    credentials = {}
    dotenv_path = Path(".") / ".env"
    
    if not dotenv_path.exists():
        return credentials
    
    try:
        with open(dotenv_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                # Map to platform
                platform_mappings = {
                    "NETLIFY_AUTH_TOKEN": "netlify",
                    "NETLIFY_TOKEN": "netlify",
                    "VERCEL_TOKEN": "vercel",
                    "NOW_TOKEN": "vercel",
                    "GITHUB_TOKEN": "github",
                    "GH_TOKEN": "github",
                    "GITHUB_PAT": "github",
                    "RENDER_API_KEY": "render",
                    "RENDER_TOKEN": "render",
                    "SURGE_TOKEN": "surge",
                }
                
                if key in platform_mappings:
                    credentials[platform_mappings[key]] = value
                    
    except Exception:
        pass
    
    return credentials


def _scan_config_files() -> Dict[str, str]:
    """Scan platform-specific config files."""
    credentials = {}
    
    # Netlify config
    netlify_config = Path.home() / ".netlify" / "config.json"
    if netlify_config.exists():
        try:
            with open(netlify_config, 'r') as f:
                config = json.load(f)
                if "auth" in config:
                    credentials["netlify"] = config["auth"]
                elif "token" in config:
                    credentials["netlify"] = config["token"]
        except Exception:
            pass
    
    # Vercel config
    vercel_config = Path.home() / ".vercel" / "config.json"
    if vercel_config.exists():
        try:
            with open(vercel_config, 'r') as f:
                config = json.load(f)
                if "token" in config:
                    credentials["vercel"] = config["token"]
                elif "user" in config and "token" in config["user"]:
                    credentials["vercel"] = config["user"]["token"]
        except Exception:
            pass
    
    # GitHub CLI config
    gh_config = Path.home() / ".config" / "gh" / "hosts.yml"
    if gh_config.exists():
        try:
            with open(gh_config, 'r') as f:
                content = f.read()
                # Simple parsing for oauth_token
                for line in content.split('\n'):
                    if 'oauth_token:' in line:
                        token = line.split('oauth_token:')[1].strip()
                        credentials["github"] = token
                        break
        except Exception:
            pass
    
    # Surge config
    surge_config = Path.home() / ".surge"
    if surge_config.exists():
        try:
            with open(surge_config, 'r') as f:
                content = f.read().strip()
                if content:
                    credentials["surge"] = content
        except Exception:
            pass
    
    return credentials


def _scan_keyring() -> Dict[str, str]:
    """Scan OS keyring for credentials."""
    try:
        import keyring
        credentials = {}
        
        services = {
            "netlify": "netlify-cli",
            "vercel": "com.vercel.cli",
            "github": "github-cli",
        }
        
        for platform, service in services.items():
            try:
                token = keyring.get_password(service, "token")
                if token:
                    credentials[platform] = token
            except Exception:
                continue
        
        return credentials
        
    except ImportError:
        return {}


def validate_credential(platform: str, credential: str) -> bool:
    """
    Validate a credential by making a test API call.
    
    Args:
        platform: Platform name
        credential: Credential token
    
    Returns:
        True if credential is valid
    """
    if platform == "github":
        try:
            import httpx
            response = httpx.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {credential}"},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    elif platform == "netlify":
        try:
            import httpx
            response = httpx.get(
                "https://api.netlify.com/api/v1/user",
                headers={"Authorization": f"Bearer {credential}"},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    # Add more platforms as needed
    return True


def get_credential_status() -> Dict[str, Dict]:
    """
    Get status of all credentials.
    
    Returns:
        Dict with credential status and validation
    """
    credentials = scan_credentials()
    status = {}
    
    for platform, token in credentials.items():
        status[platform] = {
            "configured": True,
            "valid": validate_credential(platform, token),
            "masked": token[:4] + "..." + token[-4:] if len(token) > 8 else "***"
        }
    
    return status
