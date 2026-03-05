import subprocess
import os

def deploy_to_github_pages(project_info: dict, credentials: dict):
    # Check if gh CLI is available
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True)
        if result.returncode != 0:
            raise Exception("GitHub CLI not found")
    except FileNotFoundError:
        raise Exception("GitHub CLI not installed")
    
    # Check credentials
    if not credentials.get("github"):
        raise Exception("GitHub token required")
    
    # Deploy using GitHub Pages
    try:
        cmd = ["gh", "pages", "deploy"]
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = credentials["github"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            return {
                "platform": "github_pages",
                "deployment_url": result.stdout.strip(),
                "logs": result.stderr,
                "success": True
            }
        else:
            raise Exception(f"Deployment failed: {result.stderr}")
    except Exception as e:
        return {
            "platform": "github_pages",
            "deployment_url": None,
            "logs": str(e),
            "success": False
        }
