from src.memory.deployment_failure_store import store_failure
from src.memory.project_pattern_graph import update_project_pattern
from src.memory.platform_library import update_build_strategy
from src.memory.meta_learner import update_meta_learning

class LearnAgent:
    def __init__(self):
        self.failure_memory = []
        self.pattern_graph = {}
        self.build_library = {}
        self.meta_index = {}
    
    def learn_from_deployment(self, project_type: str, platform: str, build_command: str,
                             error_message: str, failure_stage: int, fix_applied: str,
                             cycles_to_stable: int):
        # Store failure pattern
        store_failure(project_type, platform, build_command, error_message,
                     failure_stage, fix_applied, cycles_to_stable)
        
        # Update project pattern graph
        update_project_pattern(project_type, platform, "failure", failure_stage)
        
        # Update build strategy library
        update_build_strategy(project_type, platform, build_command, {}, True, 0.0)
        
        # Update meta-learning index
        update_meta_learning(project_type, "naive", cycles_to_stable)
    
    def get_recommendation(self, project_type: str, platform: str):
        # Return recommendation based on learned patterns
        return {
            "avoid": False,
            "suggested_build_command": None,
            "notes": "Based on historical data"
        }
