import subprocess
import os

def deploy_to_netlify(project_info: dict, credentials: dict):
    # Check if netlify CLI is available
    try:
        result = subprocess.run(["netlify", "--version"], capture_output=True)
        if result.returncode != 0:
            raise Exception("Netlify CLI not found")
    except FileNotFoundError:
        raise Exception("Netlify CLI not installed")
    
    # Check credentials
    if not credentials.get("netlify"):
        raise Exception("Netlify token required")
    
    # Deploy using netlify CLI
    try:
        cmd = ["netlify", "deploy"]
        env = os.environ.copy()
        env["NETLIFY_AUTH_TOKEN"] = credentials["netlify"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            return {
                "platform": "netlify",
                "deployment_url": result.stdout.strip(),
                "logs": result.stderr,
                "success": True
            }
        else:
            raise Exception(f"Deployment failed: {result.stderr}")
    except Exception as e:
        return {
            "platform": "netlify",
            "deployment_url": None,
            "logs": str(e),
            "success": False
        }
