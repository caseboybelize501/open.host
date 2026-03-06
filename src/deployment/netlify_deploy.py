import subprocess
import os
import time
from typing import Dict, Optional
from pathlib import Path


def deploy_to_netlify(project_info: Dict, credentials: Dict) -> Dict:
    """
    Deploy project to Netlify.
    
    Supports:
    - Static sites
    - React/Vue/Angular SPAs
    - Next.js, Gatsby, Nuxt
    - Node.js functions
    
    Args:
        project_info: Project metadata from project_agent
        credentials: Dict with 'netlify' token
    
    Returns:
        Deployment result with url, success status, and metadata
    """
    result = {
        "platform": "netlify",
        "success": False,
        "url": None,
        "deployment_id": None,
        "logs": [],
        "error": None,
        "timestamp": time.time()
    }
    
    project_path = project_info.get("source_dir", ".")
    build_command = project_info.get("build_command", "npm run build")
    output_dir = project_info.get("output_dir", "dist")
    
    # Check if Netlify CLI is available
    if not _check_netlify_cli():
        result["error"] = "Netlify CLI not found. Install with: npm install -g netlify-cli"
        return result
    
    # Check credentials
    auth_token = credentials.get("netlify") or os.getenv("NETLIFY_AUTH_TOKEN")
    if not auth_token:
        result["error"] = "Netlify authentication token required"
        return result
    
    try:
        # Set auth token in environment
        env = os.environ.copy()
        env["NETLIFY_AUTH_TOKEN"] = auth_token
        
        # Check if project is already linked
        linked = _check_netlify_link(project_path)
        
        if not linked:
            # Initialize new site
            init_result = _init_netlify_site(project_path, env)
            if not init_result["success"]:
                result["error"] = init_result["error"]
                return result
            result["logs"].append(f"Initialized new site: {init_result.get('site_id')}")
        
        # Run build command
        build_result = _run_netlify_build(project_path, build_command, env)
        if not build_result["success"]:
            result["error"] = f"Build failed: {build_result['error']}"
            result["logs"].extend(build_result.get("logs", []))
            return result
        result["logs"].append("Build completed successfully")
        
        # Deploy
        deploy_result = _execute_netlify_deploy(project_path, env, output_dir)
        if not deploy_result["success"]:
            result["error"] = f"Deploy failed: {deploy_result['error']}"
            result["logs"].extend(deploy_result.get("logs", []))
            return result
        
        result["url"] = deploy_result.get("url")
        result["deployment_id"] = deploy_result.get("deployment_id")
        result["logs"].extend(deploy_result.get("logs", []))
        result["success"] = True
        
        # Calculate performance score based on deploy time
        result["performance_score"] = _calculate_performance_score(deploy_result.get("deploy_time", 60))
        
    except Exception as e:
        result["error"] = str(e)
        result["logs"].append(f"Exception: {str(e)}")
    
    return result


def _check_netlify_cli() -> bool:
    """Check if Netlify CLI is installed."""
    try:
        result = subprocess.run(
            ["netlify", "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_netlify_link(project_path: str) -> bool:
    """Check if project is linked to a Netlify site."""
    netlify_config = Path(project_path) / "netlify.toml"
    if netlify_config.exists():
        return True
    
    try:
        env = os.environ.copy()
        result = subprocess.run(
            ["netlify", "status"],
            cwd=project_path,
            capture_output=True,
            timeout=30,
            env=env
        )
        return result.returncode == 0
    except Exception:
        return False


def _init_netlify_site(project_path: str, env: Dict) -> Dict:
    """Initialize a new Netlify site."""
    try:
        # Create site and capture output
        result = subprocess.run(
            ["netlify", "init", "--force"],
            cwd=project_path,
            capture_output=True,
            timeout=60,
            env=env
        )
        
        if result.returncode == 0:
            # Parse site ID from output
            output = result.stdout.decode()
            site_id = "unknown"
            return {"success": True, "site_id": site_id}
        else:
            return {"success": False, "error": result.stderr.decode()}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def _run_netlify_build(project_path: str, build_command: str, env: Dict) -> Dict:
    """Run build command."""
    try:
        result = subprocess.run(
            build_command,
            shell=True,
            cwd=project_path,
            capture_output=True,
            timeout=300,  # 5 minute timeout
            env=env
        )
        
        logs = []
        if result.stdout:
            logs.extend(result.stdout.decode().split('\n'))
        if result.stderr:
            logs.extend(result.stderr.decode().split('\n'))
        
        return {
            "success": result.returncode == 0,
            "logs": logs,
            "error": None if result.returncode == 0 else "Build failed"
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Build timed out (5 minutes)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_netlify_deploy(project_path: str, env: Dict, output_dir: str) -> Dict:
    """Execute deployment."""
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["netlify", "deploy", "--prod", "--dir", output_dir],
            cwd=project_path,
            capture_output=True,
            timeout=120,
            env=env
        )
        
        deploy_time = time.time() - start_time
        logs = []
        url = None
        deployment_id = None
        
        if result.stdout:
            output = result.stdout.decode()
            logs.append(output)
            
            # Parse URL from output
            if "Website URL:" in output:
                for line in output.split('\n'):
                    if "Website URL:" in line:
                        url = line.split("Website URL:")[1].strip()
            
            # Parse deployment ID
            if "Deployment ID:" in output:
                for line in output.split('\n'):
                    if "Deployment ID:" in line:
                        deployment_id = line.split("Deployment ID:")[1].strip()
        
        return {
            "success": result.returncode == 0,
            "logs": logs,
            "url": url,
            "deployment_id": deployment_id,
            "deploy_time": deploy_time,
            "error": None if result.returncode == 0 else result.stderr.decode()
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Deploy timed out (2 minutes)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _calculate_performance_score(deploy_time: float) -> float:
    """Calculate performance score based on deploy time."""
    # Score from 0-1 based on deploy time
    # < 30s = 1.0, 60s = 0.5, > 120s = 0.0
    if deploy_time < 30:
        return 1.0
    elif deploy_time < 60:
        return 0.8
    elif deploy_time < 90:
        return 0.5
    elif deploy_time < 120:
        return 0.3
    else:
        return 0.1
