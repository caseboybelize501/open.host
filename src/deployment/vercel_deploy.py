import subprocess
import os

def deploy_to_vercel(project_info: dict, credentials: dict):
    # Check if vercel CLI is available
    try:
        result = subprocess.run(["vercel", "--version"], capture_output=True)
        if result.returncode != 0:
            raise Exception("Vercel CLI not found")
    except FileNotFoundError:
        raise Exception("Vercel CLI not installed")
    
    # Check credentials
    if not credentials.get("vercel"):
        raise Exception("Vercel token required")
    
    # Deploy using vercel CLI
    try:
        cmd = ["vercel"]
        env = os.environ.copy()
        env["VERCEL_TOKEN"] = credentials["vercel"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            return {
                "platform": "vercel",
                "deployment_url": result.stdout.strip(),
                "logs": result.stderr,
                "success": True
            }
        else:
            raise Exception(f"Deployment failed: {result.stderr}")
    except Exception as e:
        return {
            "platform": "vercel",
            "deployment_url": None,
            "logs": str(e),
            "success": False
        }
