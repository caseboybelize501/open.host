from typing import Dict, Optional
from src.validation.cycle_manager import run_validation_cycle, get_validation_summary


class ValidationOrchestrator:
    """
    Orchestrates the 10-stage validation cycle for deployments.
    
    Responsibilities:
    - Run complete validation cycle
    - Track validation history
    - Report validation results
    - Trigger re-validation on demand
    """
    
    def __init__(self):
        self.validation_history: Dict[str, Dict] = {}
    
    def validate_deployment(self, deployment_url: str, project_type: str,
                           deployment_id: Optional[str] = None) -> Dict:
        """
        Run complete 10-stage validation cycle for a deployment.
        
        Stages:
        1. Lint - ESLint/TypeCheck passes
        2. Build - Build command succeeds
        3. Deploy - Successfully deploys to free tier
        4. Health Check - GET / returns 200
        5. SSL Check - HTTPS enforced
        6. Performance - Lighthouse score >= 80
        7. Functionality - Core features work
        8. Cost Verify - Confirmed free tier
        9. Rollback Test - Can rollback
        10. Regression - Prior stable designs pass
        
        Args:
            deployment_url: URL of deployed application
            project_type: Type of project being validated
            deployment_id: Optional deployment identifier
        
        Returns:
            Validation results with all stage outcomes
        """
        # Run the validation cycle
        results = run_validation_cycle(deployment_url, project_type, deployment_id)
        
        # Store in history
        if deployment_id:
            self.validation_history[deployment_id] = {
                "url": deployment_url,
                "project_type": project_type,
                "results": results,
                "timestamp": self._get_timestamp()
            }
        
        return results
    
    def get_validation_history(self, deployment_id: Optional[str] = None) -> Dict:
        """Get validation history, optionally filtered by deployment ID."""
        if deployment_id:
            return self.validation_history.get(deployment_id, {})
        return {"history": self.validation_history}
    
    def get_validation_summary(self) -> Dict:
        """Get summary of all validations."""
        return get_validation_summary()
    
    def revalidate(self, deployment_id: str, deployment_url: str, 
                   project_type: str) -> Dict:
        """
        Re-run validation for an existing deployment.
        
        Useful for:
        - Checking if deployment is still healthy
        - Verifying after platform changes
        - Periodic health checks
        """
        results = run_validation_cycle(deployment_url, project_type, deployment_id)
        
        # Update history
        self.validation_history[deployment_id] = {
            "url": deployment_url,
            "project_type": project_type,
            "results": results,
            "timestamp": self._get_timestamp(),
            "revalidation": True
        }
        
        return results
    
    def get_stage_details(self, stage_number: int) -> Dict:
        """Get detailed information about a specific validation stage."""
        stages = {
            1: {
                "name": "lint_project",
                "description": "ESLint/TypeCheck passes with 0 errors",
                "tools": ["eslint", "tsc"],
                "pass_criteria": "No linting errors or type errors"
            },
            2: {
                "name": "build_project",
                "description": "Build command succeeds",
                "tools": ["npm", "yarn", "pip"],
                "pass_criteria": "Build completes without errors"
            },
            3: {
                "name": "deploy_to_free_tier",
                "description": "Successfully deploys to free tier",
                "tools": ["netlify-cli", "vercel-cli", "render-cli"],
                "pass_criteria": "Deployment succeeds, no payment required"
            },
            4: {
                "name": "health_check",
                "description": "GET / returns 200 OK",
                "tools": ["httpx", "curl"],
                "pass_criteria": "HTTP 200 response from root URL"
            },
            5: {
                "name": "ssl_check",
                "description": "HTTPS enforced with valid certificate",
                "tools": ["openssl", "ssl-labs"],
                "pass_criteria": "Valid SSL certificate, HTTPS redirect"
            },
            6: {
                "name": "performance_baseline",
                "description": "Lighthouse score >= 80",
                "tools": ["lighthouse", "pagespeed"],
                "pass_criteria": "Performance score >= 80"
            },
            7: {
                "name": "functionality_test",
                "description": "Core features pass smoke tests",
                "tools": ["playwright", "cypress"],
                "pass_criteria": "All smoke tests pass"
            },
            8: {
                "name": "cost_verification",
                "description": "Confirmed free tier, no charges",
                "tools": ["platform-api"],
                "pass_criteria": "No billing events, within free limits"
            },
            9: {
                "name": "rollback_test",
                "description": "Can rollback to previous deployment",
                "tools": ["platform-cli"],
                "pass_criteria": "Rollback succeeds, site functional"
            },
            10: {
                "name": "regression",
                "description": "Prior STABLE designs still pass",
                "tools": ["internal"],
                "pass_criteria": "All previously stable deployments pass health check"
            }
        }
        
        return stages.get(stage_number, {"error": f"Unknown stage: {stage_number}"})
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# Global instance
validation_orchestrator = ValidationOrchestrator()


def validate_deployment(deployment_url: str, project_type: str,
                       deployment_id: Optional[str] = None) -> Dict:
    """Convenience function to validate deployment."""
    return validation_orchestrator.validate_deployment(
        deployment_url, project_type, deployment_id
    )


def get_validation_history(deployment_id: Optional[str] = None) -> Dict:
    """Get validation history."""
    return validation_orchestrator.get_validation_history(deployment_id)


def get_validation_summary() -> Dict:
    """Get validation summary."""
    return validation_orchestrator.get_validation_summary()
