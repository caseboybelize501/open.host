"""
Master Agent - Multi-Agent LLM Orchestrator

The Master Agent is the central intelligence that:
1. Receives tasks from GitHub scanner
2. Uses large GGUF model (7B+) for complex reasoning
3. Delegates subtasks to specialized small agents
4. Tracks job progress and makes go/no-go decisions
5. Only processes "profitable" repos
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from src.llm.llm_engine import get_llm, chat, extract_json
from src.github.github_scanner import GitHubRepo, RepoAnalysis, get_github_scanner
from src.memory.deployment_failure_store import failure_store
from src.memory.platform_library import library


@dataclass
class Job:
    """Represents a deployment job."""
    id: str
    repo_name: str
    repo_url: str
    status: str  # pending, analyzing, deploying, deployed, failed, skipped
    profitable: bool
    profit_score: float
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    assigned_agent: Optional[str] = None
    analysis: Optional[RepoAnalysis] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    skip_reason: Optional[str] = None


@dataclass
class JobDecision:
    """Decision from Master Agent about a job."""
    job_id: str
    action: str  # proceed, skip, defer, escalate
    reasoning: str
    assigned_agent: Optional[str] = None
    priority: str = "normal"  # low, normal, high, critical
    estimated_tokens: int = 512


class MasterAgent:
    """
    Master Agent for multi-agent LLM orchestration.
    
    Uses large GGUF models for:
    - Complex reasoning about repo profitability
    - Task decomposition and delegation
    - Go/no-go decisions
    - Priority assignment
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.github_scanner = get_github_scanner()
        
        # Job tracking
        self.jobs: Dict[str, Job] = {}
        self.job_queue: List[str] = []  # Job IDs pending processing
        self.completed_jobs: List[str] = []
        
        # Agent references (set by orchestrator)
        self.analyzer_agent = None
        self.deploy_agent = None
        self.memory_agent = None
        
        # Configuration
        self.min_profit_score = 5.0  # Minimum score to process
        self.max_concurrent_jobs = 3
        self.auto_process_profitable = True
    
    def scan_and_create_jobs(self, github_username: str,
                            in_progress_registry: List[str]) -> Dict:
        """
        Scan GitHub user and create jobs for profitable repos.
        
        Args:
            github_username: GitHub username to scan
            in_progress_registry: List of repo names already being processed
        
        Returns:
            Scan results with created jobs
        """
        # Scan GitHub
        scan_result = self.github_scanner.scan_user_for_jobs(
            github_username,
            in_progress_registry
        )
        
        # Create jobs for profitable repos
        created_jobs = []
        for profitable in scan_result.get("profitable_repos", []):
            repo = profitable["repo"]
            analysis = profitable["analysis"]
            
            job = self.create_job(repo, analysis)
            created_jobs.append(job)
        
        return {
            "scan_result": scan_result,
            "created_jobs": [j.id for j in created_jobs],
            "total_profitable": len(created_jobs)
        }
    
    def create_job(self, repo: GitHubRepo, analysis: RepoAnalysis) -> Job:
        """Create a new job from repo analysis."""
        job = Job(
            id=str(uuid.uuid4()),
            repo_name=repo.name,
            repo_url=repo.html_url,
            status="pending",
            profitable=analysis.profitable,
            profit_score=analysis.profit_score,
            analysis=analysis
        )
        
        self.jobs[job.id] = job
        
        if self.auto_process_profitable and analysis.profitable:
            self.job_queue.append(job.id)
        
        return job
    
    def decide_job(self, job_id: str) -> JobDecision:
        """
        Use Master Agent LLM to decide on a job.
        
        Args:
            job_id: Job to evaluate
        
        Returns:
            JobDecision with action and reasoning
        """
        job = self.jobs.get(job_id)
        if not job:
            return JobDecision(
                job_id=job_id,
                action="skip",
                reasoning="Job not found"
            )
        
        # Build context for LLM
        context = self._build_job_context(job)
        
        # Use LLM for decision
        prompt = f"""You are the Master Agent deciding on deployment jobs.

Analyze this job and decide whether to proceed, skip, defer, or escalate.

{context}

Respond with JSON:
{{
    "action": "proceed|skip|defer|escalate",
    "reasoning": "brief explanation",
    "assigned_agent": "analyzer|deploy|memory|null",
    "priority": "low|normal|high|critical",
    "estimated_tokens": 512
}}"""

        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["proceed", "skip", "defer", "escalate"]},
                "reasoning": {"type": "string"},
                "assigned_agent": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "normal", "high", "critical"]},
                "estimated_tokens": {"type": "integer"}
            },
            "required": ["action", "reasoning"]
        }

        result = extract_json(prompt, schema)
        
        if not result:
            # Fallback decision
            return self._fallback_decision(job)
        
        return JobDecision(
            job_id=job_id,
            action=result.get("action", "skip"),
            reasoning=result.get("reasoning", ""),
            assigned_agent=result.get("assigned_agent"),
            priority=result.get("priority", "normal"),
            estimated_tokens=result.get("estimated_tokens", 512)
        )
    
    def _build_job_context(self, job: Job) -> str:
        """Build context string for LLM decision."""
        analysis = job.analysis
        if not analysis:
            return f"Job: {job.repo_name}\nNo analysis available."
        
        context_parts = [
            f"Repository: {job.repo_name}",
            f"URL: {job.repo_url}",
            f"Profit Score: {job.profit_score}/10",
            f"Profitable: {job.profitable}",
            f"Tech Stack: {', '.join(analysis.tech_stack)}",
            f"Framework: {analysis.framework or 'Unknown'}",
            f"Deployment Ready: {analysis.deployment_ready}",
            f"Complexity: {analysis.estimated_complexity}",
            f"Recommended Platform: {analysis.recommended_platform or 'Unknown'}",
            f"Risk Factors: {', '.join(analysis.risk_factors) or 'None'}",
            f"Reasoning: {analysis.reasoning}",
        ]
        
        # Add historical data
        if failure_store.failures:
            similar_failures = [
                f for f in failure_store.failures
                if any(t in f.get("project_type", "").lower() for t in analysis.tech_stack)
            ]
            if similar_failures:
                context_parts.append(f"Similar Historical Failures: {len(similar_failures)}")
        
        return "\n".join(context_parts)
    
    def _fallback_decision(self, job: Job) -> JobDecision:
        """Fallback decision without LLM."""
        if not job.profitable:
            return JobDecision(
                job_id=job.id,
                action="skip",
                reasoning=f"Profit score {job.profit_score} below threshold {self.min_profit_score}"
            )
        
        if job.profit_score >= 8.0:
            return JobDecision(
                job_id=job.id,
                action="proceed",
                reasoning="High profit score",
                assigned_agent="deploy",
                priority="high"
            )
        
        return JobDecision(
            job_id=job.id,
            action="proceed",
            reasoning="Profitable repo",
            assigned_agent="analyzer",
            priority="normal"
        )
    
    def execute_decision(self, decision: JobDecision) -> Dict:
        """
        Execute decision by delegating to appropriate agent.
        
        Args:
            decision: JobDecision from Master Agent
        
        Returns:
            Execution result
        """
        job = self.jobs.get(decision.job_id)
        if not job:
            return {"success": False, "error": "Job not found"}
        
        if decision.action == "skip":
            job.status = "skipped"
            job.skip_reason = decision.reasoning
            return {"success": False, "skipped": True, "reason": decision.reasoning}
        
        if decision.action == "defer":
            job.status = "deferred"
            return {"success": False, "deferred": True}
        
        if decision.action == "escalate":
            # Would notify human operator
            job.status = "escalated"
            return {"success": False, "escalated": True}
        
        # Proceed with assigned agent
        job.status = "analyzing"
        job.assigned_agent = decision.assigned_agent
        
        if decision.assigned_agent == "analyzer" and self.analyzer_agent:
            return self.analyzer_agent.analyze_repo_job(job)
        elif decision.assigned_agent == "deploy" and self.deploy_agent:
            return self.deploy_agent.execute_deployment(job)
        else:
            # Default to analyzer
            if self.analyzer_agent:
                return self.analyzer_agent.analyze_repo_job(job)
            return {"success": False, "error": "No agent available"}
    
    def process_job_queue(self) -> List[Dict]:
        """
        Process all jobs in queue.
        
        Returns:
            List of execution results
        """
        results = []
        
        while self.job_queue and len(self.completed_jobs) < self.max_concurrent_jobs:
            job_id = self.job_queue.pop(0)
            
            # Make decision
            decision = self.decide_job(job_id)
            
            # Execute decision
            result = self.execute_decision(decision)
            results.append(result)
            
            # Update job status
            job = self.jobs[job_id]
            if result.get("success"):
                job.status = "completed"
                job.completed_at = time.time()
                self.completed_jobs.append(job_id)
            elif result.get("error"):
                job.error = result.get("error")
                job.status = "failed"
        
        return results
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a specific job."""
        job = self.jobs.get(job_id)
        if not job:
            return None
        
        return {
            "id": job.id,
            "repo_name": job.repo_name,
            "repo_url": job.repo_url,
            "status": job.status,
            "profitable": job.profitable,
            "profit_score": job.profit_score,
            "assigned_agent": job.assigned_agent,
            "created_at": datetime.fromtimestamp(job.created_at).isoformat(),
            "completed_at": datetime.fromtimestamp(job.completed_at).isoformat() if job.completed_at else None,
            "error": job.error,
            "skip_reason": job.skip_reason
        }
    
    def get_queue_status(self) -> Dict:
        """Get status of job queue."""
        return {
            "pending_jobs": len(self.job_queue),
            "total_jobs": len(self.jobs),
            "completed_jobs": len(self.completed_jobs),
            "max_concurrent": self.max_concurrent_jobs,
            "jobs": [self.get_job_status(jid) for jid in self.job_queue[:10]]
        }
    
    def set_agents(self, analyzer=None, deploy=None, memory=None):
        """Set agent references."""
        self.analyzer_agent = analyzer
        self.deploy_agent = deploy
        self.memory_agent = memory


# Global master agent instance
_master_agent: Optional[MasterAgent] = None


def get_master_agent() -> MasterAgent:
    """Get global Master Agent instance."""
    global _master_agent
    if _master_agent is None:
        _master_agent = MasterAgent()
    return _master_agent
