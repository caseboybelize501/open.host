import subprocess
import os
import time
from typing import Dict


def deploy_to_render(project_info: Dict, credentials: Dict) -> Dict:
    """
    Deploy project to Render.
    
    Supports:
    - Node.js services
    - Python services
    - Docker containers
    - Static sites
    - Go services
    - Rust services
    
    Args:
        project_info: Project metadata from project_agent
        credentials: Dict with 'render' API key
    
    Returns:
        Deployment result with url, success status, and metadata
    """
    result = {
        "platform": "render",
        "success": False,
        "url": None,
        "deployment_id": None,
        "logs": [],
        "error": None,
        "timestamp": time.time(),
        "performance_score": 0.0
    }
    
    project_path = project_info.get("source_dir", ".")
    project_type = project_info.get("project_type", "unknown")
    build_command = project_info.get("build_command", "")
    
    # Check credentials
    api_key = credentials.get("render") or os.getenv("RENDER_API_KEY")
    if not api_key:
        result["error"] = "Render API key required"
        return result
    
    # Check if Render CLI is available, otherwise use API
    if _check_render_cli():
        return _deploy_with_cli(project_path, project_type, build_command, api_key, result)
    else:
        return _deploy_with_api(project_path, project_type, build_command, api_key, result)


def _check_render_cli() -> bool:
    """Check if Render CLI is installed."""
    try:
        result = subprocess.run(
            ["render", "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _deploy_with_cli(project_path: str, project_type: str, 
                     build_command: str, api_key: str, result: Dict) -> Dict:
    """Deploy using Render CLI."""
    try:
        env = os.environ.copy()
        env["RENDER_API_KEY"] = api_key
        
        # Deploy
        deploy_result = subprocess.run(
            ["render", "deploy"],
            cwd=project_path,
            capture_output=True,
            timeout=300,
            env=env
        )
        
        logs = []
        url = None
        deployment_id = None
        
        if deploy_result.stdout:
            output = deploy_result.stdout.decode()
            logs.append(output)
            
            # Parse URL from output
            for line in output.split('\n'):
                if 'onrender.com' in line and 'http' in line:
                    url = line.strip()
                if 'Deployment ID:' in line:
                    deployment_id = line.split('Deployment ID:')[1].strip()
        
        result["success"] = deploy_result.returncode == 0
        result["url"] = url
        result["deployment_id"] = deployment_id or f"render-{int(time.time())}"
        result["logs"] = logs
        result["error"] = deploy_result.stderr.decode() if deploy_result.returncode != 0 else None
        result["performance_score"] = 0.7 if result["success"] else 0.0
        
    except subprocess.TimeoutExpired:
        result["error"] = "Deploy timed out (5 minutes)"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def _deploy_with_api(project_path: str, project_type: str, 
                     build_command: str, api_key: str, result: Dict) -> Dict:
    """Deploy using Render API."""
    try:
        import httpx
        
        # Get or create service
        service_name = os.path.basename(project_path) or f"service-{int(time.time())}"
        
        # Create service payload
        service_type = _get_render_service_type(project_type)
        payload = {
            "name": service_name,
            "type": service_type,
            "region": "oregon",
            "branch": "main",
            "buildCommand": build_command if project_type != "static" else "",
            "startCommand": _get_start_command(project_type) if project_type not in ["static"] else "",
            "staticPublishPath": project_path if project_type == "static" else None
        }
        
        # Create service via API
        response = httpx.post(
            "https://api.render.com/v1/services",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            service_data = response.json()
            result["url"] = service_data.get("service", {}).get("url")
            result["deployment_id"] = service_data.get("service", {}).get("id")
            result["success"] = True
            result["logs"].append(f"Service created: {service_name}")
            result["performance_score"] = 0.7
        else:
            result["error"] = f"API error: {response.status_code}"
            result["logs"].append(response.text)
            
    except httpx.TimeoutException:
        result["error"] = "API request timed out"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def _get_render_service_type(project_type: str) -> str:
    """Map project type to Render service type."""
    mapping = {
        "node": "web",
        "python": "web",
        "docker": "web",
        "go": "web",
        "rust": "web",
        "static": "static",
    }
    return mapping.get(project_type, "web")


def _get_start_command(project_type: str) -> str:
    """Get start command for project type."""
    mapping = {
        "node": "npm start",
        "python": "python app.py",
        "go": "./app",
        "rust": "./target/release/app",
    }
    return mapping.get(project_type, "")
