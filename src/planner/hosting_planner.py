from typing import Dict, List, Optional
from src.bootstrap.system_profile import HostingSystemProfile
from src.agents.project_agent import analyze_project
from src.agents.platform_agent import match_platforms, get_recommended_platform
from src.agents.learn_agent import LearnAgent


class HostingPlanner:
    """
    Plans deployments by analyzing projects and matching to platforms.
    
    Uses memory-informed recommendations to select best platform
    based on historical success patterns.
    """
    
    def __init__(self):
        self.learn_agent = LearnAgent()
    
    def plan_deployment(self, project_path: str, 
                       memory_recommendation: Optional[Dict] = None) -> Dict:
        """
        Create deployment plan for a project.
        
        Steps:
        1. Analyze project structure and type
        2. Query memory for historical patterns
        3. Match to compatible platforms
        4. Rank platforms by compatibility + memory success
        5. Return deployment plan with credentials
        
        Args:
            project_path: Path to project directory
            memory_recommendation: Optional recommendation from memory query
        
        Returns:
            Deployment plan with project info, platforms, and credentials
        """
        # Get current system profile
        profile = HostingSystemProfile()
        
        # Analyze project
        project_info = analyze_project(project_path)
        
        # Check for analysis errors
        if project_info.get("error"):
            return {
                "error": project_info["error"],
                "project": project_info,
                "platforms": [],
                "credentials": {}
            }
        
        project_type = project_info.get("project_type", "unknown")
        framework = project_info.get("framework")
        platform_hints = project_info.get("platform_hints", [])
        
        # Get memory-based recommendation if not provided
        if not memory_recommendation:
            memory_recommendation = self.learn_agent.get_recommendation(project_type)
        
        # Match platforms
        matched_platforms = self._match_platforms_with_memory(
            project_type=project_type,
            framework=framework,
            platform_hints=platform_hints,
            memory_recommendation=memory_recommendation
        )
        
        # Build deployment plan
        plan = {
            "project": project_info,
            "platforms": matched_platforms,
            "credentials": profile.credentials if hasattr(profile, 'credentials') else {},
            "memory_recommendation": memory_recommendation,
            "recommended_platform": matched_platforms[0] if matched_platforms else None,
            "plan_metadata": {
                "project_path": project_path,
                "project_type": project_type,
                "framework": framework,
                "platform_hints": platform_hints,
                "memory_confidence": memory_recommendation.get("confidence", 0.5)
            }
        }
        
        return plan
    
    def _match_platforms_with_memory(self, project_type: str, framework: Optional[str],
                                     platform_hints: List[str],
                                     memory_recommendation: Dict) -> List[Dict]:
        """
        Match platforms using both capability matching and memory patterns.
        
        Combines:
        1. Platform capability matching (does it support this type?)
        2. Memory success patterns (what worked before?)
        3. Memory failure avoidance (what failed before?)
        """
        # Get base platform matches
        platforms = match_platforms(project_type, framework, platform_hints)
        
        if not platforms:
            return []
        
        # Apply memory-based adjustments
        avoid_platforms = memory_recommendation.get("avoid_platforms", [])
        recommended_platform = memory_recommendation.get("platform")
        
        for platform in platforms:
            # Boost recommended platform
            if platform["name"] == recommended_platform:
                platform["memory_boost"] = 0.2
                platform["compatibility_score"] += 0.2
            
            # Penalize platforms to avoid
            if platform["name"] in avoid_platforms:
                platform["memory_penalty"] = 0.5
                platform["compatibility_score"] -= 0.5
            
            # Add memory notes
            if memory_recommendation.get("notes"):
                platform["memory_notes"] = memory_recommendation["notes"]
        
        # Filter out heavily penalized platforms
        platforms = [p for p in platforms if p["compatibility_score"] > 0]
        
        # Re-sort by adjusted score
        platforms.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        return platforms
    
    def get_deployment_options(self, project_path: str) -> Dict:
        """
        Get all deployment options for a project without creating a plan.
        
        Useful for showing user options before committing to deployment.
        """
        project_info = analyze_project(project_path)
        
        if project_info.get("error"):
            return {"error": project_info["error"], "options": []}
        
        project_type = project_info.get("project_type", "unknown")
        framework = project_info.get("framework")
        platform_hints = project_info.get("platform_hints", [])
        
        # Get all platform matches
        all_platforms = match_platforms(project_type, framework, platform_hints)
        
        # Get memory recommendation
        memory_rec = self.learn_agent.get_recommendation(project_type)
        
        return {
            "project_info": project_info,
            "all_options": all_platforms,
            "recommended": memory_rec,
            "memory_insights": {
                "avoid": memory_rec.get("avoid_platforms", []),
                "predicted_cycles": memory_rec.get("predicted_cycles_to_stable", 3)
            }
        }
    
    def compare_platforms(self, project_path: str, 
                         platform_names: List[str]) -> Dict:
        """
        Compare specific platforms for a project.
        
        Returns detailed comparison of requested platforms.
        """
        project_info = analyze_project(project_path)
        project_type = project_info.get("project_type", "unknown")
        framework = project_info.get("framework")
        platform_hints = project_info.get("platform_hints", [])
        
        all_platforms = match_platforms(project_type, framework, platform_hints)
        
        # Filter to requested platforms
        comparison = []
        for platform in all_platforms:
            if platform["name"] in platform_names:
                comparison.append(platform)
        
        return {
            "project_info": project_info,
            "comparison": comparison,
            "best_match": comparison[0] if comparison else None
        }


# Global instance
hosting_planner = HostingPlanner()


def plan_deployment(project_path: str, 
                   memory_recommendation: Optional[Dict] = None) -> Dict:
    """Convenience function to plan deployment."""
    return hosting_planner.plan_deployment(project_path, memory_recommendation)


def get_deployment_options(project_path: str) -> Dict:
    """Get deployment options."""
    return hosting_planner.get_deployment_options(project_path)


def compare_platforms(project_path: str, platform_names: List[str]) -> Dict:
    """Compare platforms."""
    return hosting_planner.compare_platforms(project_path, platform_names)
