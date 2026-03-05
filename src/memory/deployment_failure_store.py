from typing import Dict, List

class DeploymentFailureStore:
    def __init__(self):
        self.failures = []
    
    def store_failure(self, project_type: str, platform: str, build_command: str,
                     error_message: str, failure_stage: int, fix_applied: str,
                     cycles_to_stable: int):
        failure_record = {
            "project_type": project_type,
            "platform": platform,
            "build_command": build_command,
            "error_message": error_message,
            "failure_stage": failure_stage,
            "fix_applied": fix_applied,
            "cycles_to_stable": cycles_to_stable
        }
        
        self.failures.append(failure_record)
    
    def get_failures_for_project_type(self, project_type: str) -> List[Dict]:
        return [f for f in self.failures if f["project_type"] == project_type]
    
    def get_failures_for_platform(self, platform: str) -> List[Dict]:
        return [f for f in self.failures if f["platform"] == platform]

# Global instance
failure_store = DeploymentFailureStore()

def store_failure(project_type: str, platform: str, build_command: str,
                 error_message: str, failure_stage: int, fix_applied: str,
                 cycles_to_stable: int):
    failure_store.store_failure(project_type, platform, build_command,
                               error_message, failure_stage, fix_applied,
                               cycles_to_stable)
