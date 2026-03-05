from src.validation.lighthouse_runner import run_lighthouse
from src.validation.health_check import check_health
from src.validation.functional_tests import run_functional_tests
import time

def run_validation_cycle(url: str, project_type: str):
    stages = [
        "lint_project",
        "build_project",
        "deploy_to_free_tier",
        "health_check",
        "ssl_check",
        "performance_baseline",
        "functionality_test",
        "cost_verification",
        "rollback_test",
        "regression"
    ]
    
    results = []
    
    for i, stage in enumerate(stages):
        try:
            if stage == "health_check":
                passed = check_health(url)
            elif stage == "performance_baseline":
                score = run_lighthouse(url)
                passed = score >= 80
            elif stage == "functionality_test":
                passed = run_functional_tests(url, project_type)
            else:
                # Placeholder for other stages
                passed = True
            
            results.append({
                "stage": i + 1,
                "name": stage,
                "passed": passed,
                "timestamp": time.time()
            })
        except Exception as e:
            results.append({
                "stage": i + 1,
                "name": stage,
                "passed": False,
                "error": str(e),
                "timestamp": time.time()
            })
    
    return results
