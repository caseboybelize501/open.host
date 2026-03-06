from typing import Dict, List, Optional


class PlatformLibrary:
    """
    Build strategy library that tracks effective configurations per project type + platform.
    
    Stores:
    - Build commands that worked
    - Environment variables required
    - Success/failure outcomes
    - Performance scores
    
    Query: "What build command works for React on Vercel?"
    """
    
    def __init__(self):
        self.build_strategies: Dict[str, List[Dict]] = {}
    
    def update_build_strategy(self, project_type: str, platform: str, 
                             build_command: str, env_vars: Dict,
                             success: bool, performance_score: float):
        """
        Store or update build strategy.
        
        Args:
            project_type: Type of project (react, vue, python, etc.)
            platform: Platform name (netlify, vercel, etc.)
            build_command: Build command used
            env_vars: Environment variables used
            success: Whether deployment succeeded
            performance_score: Performance score (0-1)
        """
        key = f"{project_type}:{platform}"
        
        if key not in self.build_strategies:
            self.build_strategies[key] = []
        
        strategy = {
            "build_command": build_command,
            "env_vars": env_vars,
            "success": success,
            "performance_score": performance_score,
            "timestamp": self._get_timestamp()
        }
        
        self.build_strategies[key].append(strategy)
        
        # Keep only last 10 strategies per key to avoid unbounded growth
        if len(self.build_strategies[key]) > 10:
            self.build_strategies[key] = self.build_strategies[key][-10:]
    
    def get_best_strategy(self, project_type: str, platform: str) -> Optional[Dict]:
        """
        Get best strategy for project type + platform combination.
        
        Returns the most recent successful strategy, or most recent if no success.
        """
        key = f"{project_type}:{platform}"
        strategies = self.build_strategies.get(key, [])
        
        if not strategies:
            return None
        
        # Try to find successful strategies
        successful = [s for s in strategies if s.get("success")]
        
        if successful:
            # Return most recent successful
            return successful[-1]
        
        # No success yet, return most recent
        return strategies[-1]
    
    def get_all_strategies(self, project_type: Optional[str] = None,
                          platform: Optional[str] = None) -> Dict:
        """
        Get all strategies, optionally filtered.
        
        Args:
            project_type: Filter by project type
            platform: Filter by platform
        """
        if project_type is None and platform is None:
            return self.build_strategies
        
        filtered = {}
        for key, strategies in self.build_strategies.items():
            pt, pl = key.split(":") if ":" in key else (None, None)
            
            if project_type and pt != project_type:
                continue
            if platform and pl != platform:
                continue
            
            filtered[key] = strategies
        
        return filtered
    
    def get_success_rate(self, project_type: str, platform: str) -> float:
        """Calculate success rate for project type + platform."""
        key = f"{project_type}:{platform}"
        strategies = self.build_strategies.get(key, [])
        
        if not strategies:
            return 0.5  # Default when no data
        
        successes = sum(1 for s in strategies if s.get("success"))
        return successes / len(strategies)
    
    def get_average_performance(self, project_type: str, platform: str) -> float:
        """Calculate average performance score."""
        key = f"{project_type}:{platform}"
        strategies = self.build_strategies.get(key, [])
        
        if not strategies:
            return 0.0
        
        scores = [s.get("performance_score", 0.0) for s in strategies]
        return sum(scores) / len(scores)
    
    def get_strategy_history(self, project_type: str, platform: str) -> List[Dict]:
        """Get full strategy history for project type + platform."""
        key = f"{project_type}:{platform}"
        return self.build_strategies.get(key, [])
    
    def clear_strategies(self, project_type: Optional[str] = None,
                        platform: Optional[str] = None):
        """Clear strategies, optionally filtered."""
        if project_type is None and platform is None:
            self.build_strategies = {}
            return
        
        keys_to_remove = []
        for key in self.build_strategies:
            pt, pl = key.split(":") if ":" in key else (None, None)
            
            if project_type and pt == project_type:
                keys_to_remove.append(key)
            elif platform and pl == platform:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.build_strategies[key]
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# Global instance
library = PlatformLibrary()


def update_build_strategy(project_type: str, platform: str, build_command: str,
                         env_vars: Dict, success: bool, performance_score: float):
    """Convenience function to update strategy."""
    library.update_build_strategy(project_type, platform, build_command,
                                 env_vars, success, performance_score)


def get_best_strategy(project_type: str, platform: str) -> Optional[Dict]:
    """Get best strategy."""
    return library.get_best_strategy(project_type, platform)


def get_all_strategies(project_type: Optional[str] = None,
                      platform: Optional[str] = None) -> Dict:
    """Get all strategies."""
    return library.get_all_strategies(project_type, platform)


def get_success_rate(project_type: str, platform: str) -> float:
    """Get success rate."""
    return library.get_success_rate(project_type, platform)
