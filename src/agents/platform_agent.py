from typing import Dict, List, Optional
from src.bootstrap.system_profile import HostingSystemProfile


class PlatformMatcher:
    """
    Matches projects to suitable hosting platforms based on:
    - Project type and framework
    - Platform capabilities and restrictions
    - Historical success patterns (from memory)
    - Available credentials
    """
    
    def __init__(self):
        # Platform capabilities matrix
        self.platform_capabilities = {
            "netlify": {
                "supported_types": ["static", "node", "react", "vue", "angular", "svelte", "gatsby", "nuxt", "next"],
                "features": ["spa", "static", "cdn", "functions", "redirects"],
                "build_command_required": True,
                "env_vars_supported": True,
                "free_tier": {
                    "bandwidth": "100GB/month",
                    "build_minutes": "300/month",
                    "sites": "unlimited"
                },
                "best_for": ["spa", "static", "jamstack"]
            },
            "vercel": {
                "supported_types": ["static", "node", "react", "vue", "angular", "svelte", "next", "nuxt", "gatsby", "remix"],
                "features": ["spa", "static", "cdn", "serverless", "edge-functions", "preview-deployments"],
                "build_command_required": True,
                "env_vars_supported": True,
                "free_tier": {
                    "bandwidth": "100GB/month",
                    "build_minutes": "6000/month",
                    "projects": "unlimited"
                },
                "best_for": ["next", "serverless", "preview-deployments"]
            },
            "github_pages": {
                "supported_types": ["static"],
                "features": ["static", "cdn", "jekyll"],
                "build_command_required": False,
                "env_vars_supported": False,
                "free_tier": {
                    "bandwidth": "unlimited",
                    "build_minutes": "N/A",
                    "sites": "unlimited"
                },
                "best_for": ["static", "documentation", "portfolios"]
            },
            "render": {
                "supported_types": ["node", "python", "docker", "go", "rust", "static"],
                "features": ["server", "database", "docker", "cron", "background-workers"],
                "build_command_required": True,
                "env_vars_supported": True,
                "free_tier": {
                    "bandwidth": "unlimited",
                    "build_minutes": "N/A",
                    "services": "limited"
                },
                "best_for": ["server", "api", "database", "docker"]
            }
        }
    
    def match_platforms(self, project_type: str, framework: Optional[str] = None,
                       platform_hints: Optional[List[str]] = None) -> List[Dict]:
        """
        Match project to compatible platforms.
        
        Args:
            project_type: Type of project (node, python, static, etc.)
            framework: Detected framework (react, next, vue, etc.)
            platform_hints: Additional hints from project analysis
        
        Returns:
            List of compatible platforms ranked by suitability
        """
        profile = HostingSystemProfile()
        available_platforms = profile.platforms if hasattr(profile, 'platforms') else []
        
        # Determine primary matching key
        match_key = framework or project_type
        
        compatible_platforms = []
        
        for platform_name, capabilities in self.platform_capabilities.items():
            # Check if platform is available (has credentials)
            is_available = self._check_platform_available(platform_name, available_platforms)
            
            # Check if project type is supported
            type_supported = self._check_type_supported(match_key, capabilities)
            
            # Calculate compatibility score
            score = self._calculate_compatibility_score(
                platform_name, capabilities, match_key, platform_hints or []
            )
            
            if type_supported or score > 0.3:
                compatible_platforms.append({
                    "name": platform_name,
                    "available": is_available,
                    "supported_types": capabilities["supported_types"],
                    "features": capabilities["features"],
                    "free_tier": capabilities["free_tier"],
                    "best_for": capabilities["best_for"],
                    "compatibility_score": score,
                    "recommendation_reason": self._get_recommendation_reason(
                        platform_name, capabilities, match_key, platform_hints or []
                    )
                })
        
        # Sort by compatibility score (descending)
        compatible_platforms.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        return compatible_platforms
    
    def _check_platform_available(self, platform_name: str, available_platforms: List[Dict]) -> bool:
        """Check if platform has credentials configured."""
        # Check if platform is in available platforms list
        if available_platforms:
            return any(p.get("name") == platform_name for p in available_platforms)
        
        # Default: assume all platforms are potentially available
        return True
    
    def _check_type_supported(self, match_key: str, capabilities: Dict) -> bool:
        """Check if project type/framework is supported by platform."""
        supported = capabilities.get("supported_types", [])
        return match_key in supported or any(s in match_key for s in supported)
    
    def _calculate_compatibility_score(self, platform_name: str, capabilities: Dict,
                                       match_key: str, platform_hints: List[str]) -> float:
        """
        Calculate compatibility score between project and platform.
        
        Score factors:
        - Type/framework match (0-0.5)
        - Feature alignment (0-0.3)
        - Best-for match (0-0.2)
        """
        score = 0.0
        
        # Type/framework match (0-0.5)
        if match_key in capabilities["supported_types"]:
            score += 0.5
        elif any(s in match_key for s in capabilities["supported_types"]):
            score += 0.3
        
        # Feature alignment (0-0.3)
        feature_matches = sum(1 for hint in platform_hints if hint in capabilities["features"])
        if platform_hints:
            score += 0.3 * (feature_matches / len(platform_hints))
        
        # Best-for match (0-0.2)
        if match_key in capabilities["best_for"]:
            score += 0.2
        elif any(h in capabilities["best_for"] for h in platform_hints):
            score += 0.1
        
        return round(score, 2)
    
    def _get_recommendation_reason(self, platform_name: str, capabilities: Dict,
                                   match_key: str, platform_hints: List[str]) -> str:
        """Generate human-readable recommendation reason."""
        reasons = []
        
        if match_key in capabilities["supported_types"]:
            reasons.append(f"Native support for {match_key}")
        
        matching_features = [h for h in platform_hints if h in capabilities["features"]]
        if matching_features:
            reasons.append(f"Supports required features: {', '.join(matching_features)}")
        
        if match_key in capabilities["best_for"]:
            reasons.append(f"Optimized for {match_key} projects")
        
        if capabilities["free_tier"]["bandwidth"] == "unlimited":
            reasons.append("Unlimited bandwidth on free tier")
        
        return "; ".join(reasons) if reasons else "Compatible with project type"
    
    def get_platform_details(self, platform_name: str) -> Optional[Dict]:
        """Get detailed information about a specific platform."""
        if platform_name in self.platform_capabilities:
            return self.platform_capabilities[platform_name]
        return None
    
    def get_recommended_platform(self, project_type: str, framework: Optional[str] = None,
                                platform_hints: Optional[List[str]] = None) -> Optional[Dict]:
        """Get the single best recommended platform."""
        matches = self.match_platforms(project_type, framework, platform_hints)
        return matches[0] if matches else None


# Global instance
platform_matcher = PlatformMatcher()


def match_platforms(project_type: str, framework: Optional[str] = None,
                   platform_hints: Optional[List[str]] = None) -> List[Dict]:
    """Convenience function to match platforms."""
    return platform_matcher.match_platforms(project_type, framework, platform_hints)


def get_platform_details(platform_name: str) -> Optional[Dict]:
    """Get platform details."""
    return platform_matcher.get_platform_details(platform_name)


def get_recommended_platform(project_type: str, framework: Optional[str] = None) -> Optional[Dict]:
    """Get recommended platform."""
    return platform_matcher.get_recommended_platform(project_type, framework)
