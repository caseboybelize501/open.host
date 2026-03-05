from src.bootstrap.system_profile import HostingSystemProfile
from src.agents.project_agent import analyze_project
from src.agents.platform_agent import match_platforms

def plan_deployment(project_path: str):
    # Get current system profile
    profile = HostingSystemProfile()
    
    # Analyze project
    project_info = analyze_project(project_path)
    
    # Match platforms
    matched_platforms = match_platforms(project_info["project_type"])
    
    return {
        "project": project_info,
        "platforms": matched_platforms,
        "credentials": profile.credentials
    }
