import subprocess
import os

def deploy_to_render(project_info: dict, credentials: dict):
    # Check if render CLI is available
    try:
        result = subprocess.run(["render", "--version"], capture_output=True)
        if result.returncode != 0:
            raise Exception("Render CLI not found")
    except FileNotFoundError:
        raise Exception("Render CLI not installed")
    
    # Check credentials
    if not credentials.get("render"):
        raise Exception("Render token required")
    
    # Deploy using render CLI
    try:
        cmd = ["render", "deploy"]
        env = os.environ.copy()
        env["RENDER_TOKEN"] = credentials["render"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            return {
                "platform": "render",
                "deployment_url": result.stdout.strip(),
                "logs": result.stderr,
                "success": True
            }
        else:
            raise Exception(f"Deployment failed: {result.stderr}")
    except Exception as e:
        return {
            "platform": "render",
            "deployment_url": None,
            "logs": str(e),
            "success": False
        }
