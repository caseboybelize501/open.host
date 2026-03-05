from typing import Dict, List

class PlatformLibrary:
    def __init__(self):
        self.build_strategies = {}
    
    def update_build_strategy(self, project_type: str, platform: str, build_command: str,
                             env_vars: Dict, success: bool, performance_score: float):
        key = f"{project_type}:{platform}"
        if key not in self.build_strategies:
            self.build_strategies[key] = []
        
        strategy = {
            "build_command": build_command,
            "env_vars": env_vars,
            "success": success,
            "performance_score": performance_score
        }
        
        self.build_strategies[key].append(strategy)
    
    def get_best_strategy(self, project_type: str, platform: str) -> Dict:
        key = f"{project_type}:{platform}"
        strategies = self.build_strategies.get(key, [])
        
        if not strategies:
            return {}
        
        # Return the most successful strategy
        best = max(strategies, key=lambda x: x["success"])
        return best

# Global instance
library = PlatformLibrary()

def update_build_strategy(project_type: str, platform: str, build_command: str,
                         env_vars: Dict, success: bool, performance_score: float):
    library.update_build_strategy(project_type, platform, build_command,
                                 env_vars, success, performance_score)
