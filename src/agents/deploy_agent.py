import subprocess
from src.bootstrap.system_profile import HostingSystemProfile
from src.deployment.netlify_deploy import deploy_to_netlify
from src.deployment.vercel_deploy import deploy_to_vercel
from src.deployment.github_pages_deploy import deploy_to_github_pages
from src.deployment.render_deploy import deploy_to_render

def deploy_project(plan):
    project_info = plan["project"]
    platforms = plan["platforms"]
    credentials = plan["credentials"]
    
    # Try each platform in order until one succeeds
    for platform in platforms:
        try:
            if platform["name"] == "netlify":
                result = deploy_to_netlify(project_info, credentials)
            elif platform["name"] == "vercel":
                result = deploy_to_vercel(project_info, credentials)
            elif platform["name"] == "github_pages":
                result = deploy_to_github_pages(project_info, credentials)
            elif platform["name"] == "render":
                result = deploy_to_render(project_info, credentials)
            
            if result.get("success"):
                return result
        except Exception as e:
            print(f"Failed to deploy to {platform['name']}: {str(e)}")
            continue
    
    raise Exception("No platform succeeded in deployment")
