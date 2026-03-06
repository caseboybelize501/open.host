import subprocess
from typing import Dict, Optional
from src.bootstrap.system_profile import HostingSystemProfile
from src.deployment.netlify_deploy import deploy_to_netlify
from src.deployment.vercel_deploy import deploy_to_vercel
from src.deployment.github_pages_deploy import deploy_to_github_pages
from src.deployment.render_deploy import deploy_to_render
from src.memory.deployment_failure_store import failure_store
from src.memory.platform_library import library


def deploy_project(plan: Dict, deployment_id: str) -> Dict:
    """
    Deploy project using memory-informed platform selection.
    
    Before deploying:
    1. Query memory for platform success history with this project type
    2. Check for known failure patterns
    3. Apply learned build strategies
    
    Args:
        plan: Deployment plan with project info and platforms
        deployment_id: Unique deployment identifier
    
    Returns:
        Deployment result with url, status, and metadata
    """
    project_info = plan.get("project", {})
    platforms = plan.get("platforms", [])
    credentials = plan.get("credentials", {})
    
    project_type = project_info.get("project_type", "unknown")
    build_command = project_info.get("build_command", "")
    
    # Query memory for best platform for this project type
    memory_recommendation = _get_memory_recommendation(project_type, platforms)
    
    # Reorder platforms based on memory recommendation
    if memory_recommendation:
        platforms = _prioritize_platforms(platforms, memory_recommendation)
    
    # Get best build strategy from memory
    build_strategy = _get_build_strategy(project_type, platforms[0]["name"] if platforms else None)
    if build_strategy and build_strategy.get("build_command"):
        project_info["build_command"] = build_strategy["build_command"]
    
    # Track failures for learning
    last_error = None
    attempted_platforms = []
    
    # Try each platform in order until one succeeds
    for platform in platforms:
        platform_name = platform["name"]
        attempted_platforms.append(platform_name)
        
        try:
            result = _deploy_to_platform(platform_name, project_info, credentials)
            
            if result.get("success"):
                # Store successful deployment pattern
                library.update_build_strategy(
                    project_type=project_type,
                    platform=platform_name,
                    build_command=project_info.get("build_command", ""),
                    env_vars=project_info.get("environment_vars", {}),
                    success=True,
                    performance_score=result.get("performance_score", 1.0)
                )
                
                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "platform": platform_name,
                    "url": result.get("url"),
                    "build_command_used": project_info.get("build_command"),
                    "memory_recommendation_used": memory_recommendation.get("platform") if memory_recommendation else None,
                    "attempts": len(attempted_platforms),
                    "timestamp": result.get("timestamp")
                }
                
        except Exception as e:
            last_error = str(e)
            
            # Store failure in memory
            failure_store.store_failure(
                project_type=project_type,
                platform=platform_name,
                build_command=project_info.get("build_command", ""),
                error_message=last_error,
                failure_stage=3,  # Stage 3 = deploy_to_free_tier
                fix_applied="platform_switch",
                cycles_to_stable=1
            )
            
            continue
    
    # All platforms failed
    return {
        "success": False,
        "deployment_id": deployment_id,
        "error": last_error,
        "attempted_platforms": attempted_platforms,
        "memory_recommendation_used": memory_recommendation.get("platform") if memory_recommendation else None
    }


def _get_memory_recommendation(project_type: str, platforms: list) -> Optional[Dict]:
    """
    Query memory for best platform recommendation.
    
    Checks:
    1. Historical success rate per platform for this project type
    2. Known failure patterns to avoid
    3. Build strategy effectiveness
    """
    # Get best strategy from library
    best_platform = None
    best_score = -1
    
    for platform in platforms:
        platform_name = platform["name"]
        strategy = library.get_best_strategy(project_type, platform_name)
        
        if strategy and strategy.get("success"):
            # Calculate score based on historical performance
            score = strategy.get("performance_score", 0.5)
            if score > best_score:
                best_score = score
                best_platform = platform_name
    
    if best_platform:
        return {
            "platform": best_platform,
            "confidence": best_score,
            "source": "platform_library"
        }
    
    # Check failure store for platforms to avoid
    failures = failure_store.get_failures_for_project_type(project_type)
    failed_platforms = set(f["platform"] for f in failures if f.get("failure_stage") == 3)
    
    # Recommend first platform that hasn't failed
    for platform in platforms:
        if platform["name"] not in failed_platforms:
            return {
                "platform": platform["name"],
                "confidence": 0.5,
                "source": "failure_avoidance",
                "avoid_platforms": list(failed_platforms)
            }
    
    return None


def _prioritize_platforms(platforms: list, recommendation: Dict) -> list:
    """Reorder platforms based on memory recommendation."""
    recommended = recommendation.get("platform")
    avoid = recommendation.get("avoid_platforms", [])
    
    if not recommended:
        return platforms
    
    # Sort: recommended first, then others, avoiding failed platforms
    def sort_key(p):
        if p["name"] == recommended:
            return (0, p["name"])
        if p["name"] in avoid:
            return (2, p["name"])
        return (1, p["name"])
    
    return sorted(platforms, key=sort_key)


def _get_build_strategy(project_type: str, platform: Optional[str]) -> Optional[Dict]:
    """Get best build strategy from memory."""
    if not platform:
        return None
    
    return library.get_best_strategy(project_type, platform)


def _deploy_to_platform(platform_name: str, project_info: Dict, credentials: Dict) -> Dict:
    """Execute deployment to specific platform."""
    if platform_name == "netlify":
        return deploy_to_netlify(project_info, credentials)
    elif platform_name == "vercel":
        return deploy_to_vercel(project_info, credentials)
    elif platform_name == "github_pages":
        return deploy_to_github_pages(project_info, credentials)
    elif platform_name == "render":
        return deploy_to_render(project_info, credentials)
    else:
        raise ValueError(f"Unknown platform: {platform_name}")
