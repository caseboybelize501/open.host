import subprocess
import os
import time
import json
from typing import Dict, Optional
from pathlib import Path


def deploy_to_vercel(project_info: Dict, credentials: Dict) -> Dict:
    """
    Deploy project to Vercel.
    
    Supports:
    - Static sites
    - React/Vue/Angular SPAs
    - Next.js (first-class support)
    - Nuxt, Gatsby, Remix
    - Serverless functions
    
    Args:
        project_info: Project metadata from project_agent
        credentials: Dict with 'vercel' token
    
    Returns:
        Deployment result with url, success status, and metadata
    """
    result = {
        "platform": "vercel",
        "success": False,
        "url": None,
        "deployment_id": None,
        "logs": [],
        "error": None,
        "timestamp": time.time(),
        "performance_score": 0.0
    }
    
    project_path = project_info.get("source_dir", ".")
    build_command = project_info.get("build_command", "npm run build")
    framework = project_info.get("framework")
    
    # Check if Vercel CLI is available
    if not _check_vercel_cli():
        result["error"] = "Vercel CLI not found. Install with: npm install -g vercel"
        return result
    
    # Check credentials
    auth_token = credentials.get("vercel") or os.getenv("VERCEL_TOKEN")
    if not auth_token:
        result["error"] = "Vercel authentication token required"
        return result
    
    try:
        # Set auth token in environment
        env = os.environ.copy()
        env["VERCEL_TOKEN"] = auth_token
        
        # Ensure project is linked
        link_result = _link_vercel_project(project_path, env)
        if not link_result["success"]:
            result["error"] = link_result["error"]
            return result
        
        # Run build (Vercel handles build automatically, but we can pre-build)
        if build_command and framework not in ["next", "nuxt"]:
            build_result = _run_build(project_path, build_command, env)
            if not build_result["success"]:
                result["error"] = f"Build failed: {build_result['error']}"
                result["logs"].extend(build_result.get("logs", []))
                return result
            result["logs"].append("Pre-build completed successfully")
        
        # Deploy
        deploy_result = _execute_vercel_deploy(project_path, env, framework)
        if not deploy_result["success"]:
            result["error"] = f"Deploy failed: {deploy_result['error']}"
            result["logs"].extend(deploy_result.get("logs", []))
            return result
        
        result["url"] = deploy_result.get("url")
        result["deployment_id"] = deploy_result.get("deployment_id")
        result["logs"].extend(deploy_result.get("logs", []))
        result["success"] = True
        result["performance_score"] = _calculate_performance_score(deploy_result.get("deploy_time", 60))
        
    except Exception as e:
        result["error"] = str(e)
        result["logs"].append(f"Exception: {str(e)}")
    
    return result


def _check_vercel_cli() -> bool:
    """Check if Vercel CLI is installed."""
    try:
        result = subprocess.run(
            ["vercel", "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _link_vercel_project(project_path: str, env: Dict) -> Dict:
    """Link project to Vercel."""
    vercel_config = Path(project_path) / "vercel.json"
    
    # Check if already linked (vercel.json exists with projectId)
    if vercel_config.exists():
        try:
            with open(vercel_config, 'r') as f:
                config = json.load(f)
                if "projectId" in config:
                    return {"success": True, "linked": True}
        except Exception:
            pass
    
    try:
        # Link to Vercel (non-interactive mode)
        result = subprocess.run(
            ["vercel", "link", "--force"],
            cwd=project_path,
            capture_output=True,
            timeout=60,
            env=env
        )
        
        if result.returncode == 0:
            return {"success": True, "linked": True}
        else:
            # Try creating a new project
            return _create_vercel_project(project_path, env)
            
    except Exception as e:
        return _create_vercel_project(project_path, env)


def _create_vercel_project(project_path: str, env: Dict) -> Dict:
    """Create a new Vercel project."""
    try:
        result = subprocess.run(
            ["vercel"],
            cwd=project_path,
            capture_output=True,
            timeout=120,
            env=env,
            input="Y\n"  # Accept defaults
        )
        
        if result.returncode == 0:
            return {"success": True, "linked": True}
        else:
            return {"success": False, "error": result.stderr.decode()}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def _run_build(project_path: str, build_command: str, env: Dict) -> Dict:
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


def _execute_vercel_deploy(project_path: str, env: Dict, framework: Optional[str]) -> Dict:
    """Execute deployment."""
    start_time = time.time()
    
    try:
        # Use --prod for production deployment
        result = subprocess.run(
            ["vercel", "--prod", "--yes"],
            cwd=project_path,
            capture_output=True,
            timeout=180,  # 3 minute timeout
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
            # Vercel outputs like: https://project-name.vercel.app
            for line in output.split('\n'):
                if '.vercel.app' in line and 'http' in line:
                    # Extract URL
                    parts = line.strip().split()
                    for part in parts:
                        if part.startswith('https://') and 'vercel.app' in part:
                            url = part
                            break
            
            # Get deployment ID from output or API
            if 'Deployment ID:' in output:
                for line in output.split('\n'):
                    if 'Deployment ID:' in line:
                        deployment_id = line.split('Deployment ID:')[1].strip()
                        break
        
        # If URL not found in output, construct it
        if not url and result.returncode == 0:
            # Vercel typically uses project-name.vercel.app format
            url = f"https://deployment-{deployment_id[:8] if deployment_id else 'new'}.vercel.app"
        
        return {
            "success": result.returncode == 0,
            "logs": logs,
            "url": url,
            "deployment_id": deployment_id or f"vercel-{int(time.time())}",
            "deploy_time": deploy_time,
            "error": None if result.returncode == 0 else result.stderr.decode()
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Deploy timed out (3 minutes)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _calculate_performance_score(deploy_time: float) -> float:
    """Calculate performance score based on deploy time."""
    # Score from 0-1 based on deploy time
    if deploy_time < 30:
        return 1.0
    elif deploy_time < 60:
        return 0.8
    elif deploy_time < 90:
        return 0.6
    elif deploy_time < 120:
        return 0.4
    else:
        return 0.2


def get_vercel_projects(auth_token: str) -> list:
    """Get list of Vercel projects for authenticated user."""
    try:
        import httpx
        response = httpx.get(
            "https://api.vercel.com/v9/projects",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("projects", [])
    except Exception:
        pass
    return []
