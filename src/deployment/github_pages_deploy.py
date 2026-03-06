import subprocess
import os
import time
from typing import Dict


def deploy_to_github_pages(project_info: Dict, credentials: Dict) -> Dict:
    """
    Deploy project to GitHub Pages.
    
    Supports:
    - Static sites
    - Jekyll sites
    - Pre-built SPAs
    
    Args:
        project_info: Project metadata from project_agent
        credentials: Dict with 'github' token
    
    Returns:
        Deployment result with url, success status, and metadata
    """
    result = {
        "platform": "github_pages",
        "success": False,
        "url": None,
        "deployment_id": None,
        "logs": [],
        "error": None,
        "timestamp": time.time(),
        "performance_score": 0.0
    }
    
    project_path = project_info.get("source_dir", ".")
    
    # Check if git is available
    if not _check_git():
        result["error"] = "Git not found. Install git first."
        return result
    
    # Check credentials
    github_token = credentials.get("github") or os.getenv("GITHUB_TOKEN")
    if not github_token:
        result["error"] = "GitHub token required for deployment"
        return result
    
    try:
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = github_token
        
        # Get or create repository name
        repo_name = _get_repo_name(project_path) or f"pages-{int(time.time())}"
        
        # Initialize git repo if needed
        _init_git_repo(project_path)
        
        # Configure git user
        _configure_git_user(project_path, env)
        
        # Create/update gh-pages branch
        push_result = _push_to_gh_pages(project_path, repo_name, github_token, env)
        
        if not push_result["success"]:
            result["error"] = push_result["error"]
            result["logs"].extend(push_result.get("logs", []))
            return result
        
        # Construct GitHub Pages URL
        username = _get_github_username(github_token)
        if username:
            result["url"] = f"https://{username}.github.io/{repo_name}"
        else:
            result["url"] = f"https://github.com/{repo_name}"
        
        result["deployment_id"] = repo_name
        result["logs"].extend(push_result.get("logs", []))
        result["success"] = True
        result["performance_score"] = 0.8  # GitHub Pages is typically fast
        
    except Exception as e:
        result["error"] = str(e)
        result["logs"].append(f"Exception: {str(e)}")
    
    return result


def _check_git() -> bool:
    """Check if git is installed."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _get_repo_name(project_path: str) -> str:
    """Get repository name from git remote or directory."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_path,
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            url = result.stdout.decode().strip()
            # Extract repo name from URL
            if "github.com" in url:
                return url.split("/")[-1].replace(".git", "")
    except Exception:
        pass
    
    # Fall back to directory name
    return os.path.basename(project_path)


def _init_git_repo(project_path: str):
    """Initialize git repo if not exists."""
    try:
        subprocess.run(
            ["git", "init"],
            cwd=project_path,
            capture_output=True,
            timeout=10
        )
    except Exception:
        pass


def _configure_git_user(project_path: str, env: Dict):
    """Configure git user."""
    try:
        subprocess.run(
            ["git", "config", "user.name", "Open.Host Jarvis"],
            cwd=project_path,
            capture_output=True,
            timeout=10
        )
        subprocess.run(
            ["git", "config", "user.email", "jarvis@open.host"],
            cwd=project_path,
            capture_output=True,
            timeout=10
        )
    except Exception:
        pass


def _push_to_gh_pages(project_path: str, repo_name: str, 
                      github_token: str, env: Dict) -> Dict:
    """Push to gh-pages branch."""
    logs = []
    
    try:
        # Add all files
        subprocess.run(
            ["git", "add", "."],
            cwd=project_path,
            capture_output=True,
            timeout=30
        )
        
        # Commit
        subprocess.run(
            ["git", "commit", "-m", "Deploy via Open.Host Jarvis"],
            cwd=project_path,
            capture_output=True,
            timeout=30
        )
        
        # Create or checkout gh-pages branch
        subprocess.run(
            ["git", "checkout", "-b", "gh-pages"],
            cwd=project_path,
            capture_output=True,
            timeout=10
        )
        
        # Push to GitHub
        auth_url = f"https://{github_token}@github.com/{repo_name}.git"
        result = subprocess.run(
            ["git", "push", "-f", auth_url, "gh-pages"],
            cwd=project_path,
            capture_output=True,
            timeout=60,
            env=env
        )
        
        if result.stdout:
            logs.extend(result.stdout.decode().split('\n'))
        if result.stderr:
            logs.extend(result.stderr.decode().split('\n'))
        
        return {
            "success": result.returncode == 0,
            "logs": logs,
            "error": None if result.returncode == 0 else "Push failed"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "logs": logs}


def _get_github_username(github_token: str) -> str:
    """Get GitHub username from token."""
    try:
        import httpx
        response = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {github_token}"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("login")
    except Exception:
        pass
    return ""
