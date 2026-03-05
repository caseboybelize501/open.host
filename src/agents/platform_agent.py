from src.bootstrap.system_profile import HostingSystemProfile

def match_platforms(project_type: str):
    profile = HostingSystemProfile()
    
    # Get available platforms
    platforms = profile.platforms
    
    # Filter by project type support
    compatible_platforms = []
    for platform in platforms:
        if project_type in platform["supported_types"]:
            compatible_platforms.append(platform)
    
    # Rank by compatibility (simple ranking based on supported types)
    ranked_platforms = sorted(compatible_platforms, key=lambda x: len(x["supported_types"]), reverse=True)
    
    return ranked_platforms
