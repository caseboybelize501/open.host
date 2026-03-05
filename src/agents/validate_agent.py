from src.validation.cycle_manager import run_validation_cycle

def validate_deployment(deployment_url: str, project_type: str):
    # Run the 10-stage validation cycle
    results = run_validation_cycle(deployment_url, project_type)
    
    return {
        "url": deployment_url,
        "project_type": project_type,
        "stages": results,
        "overall_pass": all(stage["passed"] for stage in results)
    }
