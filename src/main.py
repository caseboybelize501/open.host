"""
Open.Host Jarvis - Main Application

Multi-Agent LLM Orchestration System for GitHub Repository Deployment

Architecture:
- Master Agent (large GGUF) - Orchestrates and makes decisions
- Analyzer Agent (small GGUF) - Code analysis and tech stack detection
- Deploy Agent - Executes deployments
- Memory Agent - 4-layer memory + drift tracking

Input: GitHub username (e.g., caseboybelize501)
Process: Scan repos → Filter profitable → Deploy
"""

import asyncio
import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Bootstrap
from src.bootstrap.system_scanner import scan_system
from src.bootstrap.system_profile import HostingSystemProfile

# LLM
from src.llm.model_pool import get_model_pool, scan_models, get_model_summary
from src.llm.llm_engine import get_llm

# GitHub
from src.github.github_scanner import get_github_scanner

# Agents
from src.agents.master_agent import get_master_agent, MasterAgent
from src.agents.analyzer_agent import get_analyzer_agent
from src.agents.memory_agent import get_memory_agent
from src.agents.deploy_agent import deploy_project

app = FastAPI(
    title="Open.Host Jarvis - Multi-Agent LLM System",
    version="2.0.0",
    description="GitHub repository scanner and deployment orchestrator using local GGUF models"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
deployments: Dict[str, Dict] = {}
system_initialized = False


# ============================================================================
# Request/Response Models
# ============================================================================

class GitHubScanRequest(BaseModel):
    """Request to scan GitHub user."""
    username: str
    min_profit_score: float = 5.0
    exclude_forks: bool = True
    exclude_archived: bool = True


class JobDecisionRequest(BaseModel):
    """Request for job decision."""
    job_id: str
    force_action: Optional[str] = None  # Override AI decision


class DeployRequest(BaseModel):
    """Request to deploy a repository."""
    repo_name: str
    repo_url: str
    platform: Optional[str] = None
    project_type: Optional[str] = None


class ModelScanRequest(BaseModel):
    """Request to scan for GGUF models."""
    custom_paths: Optional[List[str]] = None


# ============================================================================
# Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    global system_initialized
    
    print("=" * 60)
    print("OPEN.HOST JARVIS - MULTI-AGENT LLM SYSTEM")
    print("=" * 60)
    
    # Run system scan
    print("\n[1/4] Running system scan...")
    scan_system()
    
    # Scan for GGUF models
    print("\n[2/4] Scanning for GGUF models...")
    model_pool = get_model_pool()
    models = model_pool.scan_for_models()
    print(f"  Found {len(models)} GGUF models")
    
    # Initialize LLM
    print("\n[3/4] Initializing LLM engine...")
    llm = get_llm()
    
    # Initialize agents
    print("\n[4/4] Initializing agents...")
    master = get_master_agent()
    analyzer = get_analyzer_agent()
    memory = get_memory_agent()
    
    # Wire up agents
    master.set_agents(analyzer=analyzer, deploy=None, memory=memory)
    
    system_initialized = True
    
    print("\n" + "=" * 60)
    print("SYSTEM READY")
    print("=" * 60)


# ============================================================================
# System Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """System health check."""
    model_summary = get_model_summary() if system_initialized else {"total_models": 0}
    
    return {
        "status": "healthy" if system_initialized else "initializing",
        "system_initialized": system_initialized,
        "models_available": model_summary.get("total_models", 0),
        "jobs_pending": len(get_master_agent().job_queue) if system_initialized else 0,
        "jobs_completed": len(get_master_agent().completed_jobs) if system_initialized else 0
    }


@app.get("/api/system/profile")
async def get_system_profile():
    """Get system profile."""
    return HostingSystemProfile.model_dump()


# ============================================================================
# Model Management Endpoints
# ============================================================================

@app.post("/api/models/scan")
async def scan_model_paths(request: ModelScanRequest):
    """
    Scan for GGUF models on C:/ and D:/ drives.
    
    Models are automatically loaded for inference.
    """
    model_pool = get_model_pool()
    
    # Add custom paths if provided
    if request.custom_paths:
        from pathlib import Path
        for path in request.custom_paths:
            p = Path(path)
            if p.exists() and p not in model_pool.scan_paths:
                model_pool.scan_paths.append(p)
    
    # Scan
    models = model_pool.scan_for_models()
    
    return {
        "models_found": len(models),
        "models": [
            {
                "name": m.name,
                "path": m.path,
                "size_gb": m.size_gb,
                "type": m.model_type,
                "parameters": m.parameters,
                "quantization": m.quantization
            }
            for m in models
        ],
        "summary": model_pool.get_available_models_summary()
    }


@app.get("/api/models/status")
async def get_model_status():
    """Get status of loaded models."""
    return get_model_summary()


# ============================================================================
# GitHub Scanning Endpoints
# ============================================================================

@app.post("/api/github/scan")
async def scan_github_user(request: GitHubScanRequest):
    """
    Scan GitHub user repositories and create jobs for profitable ones.
    
    This is the main entry point for the autonomous workflow:
    1. Scan all repos for username
    2. Filter out forks, archived, inactive
    3. Analyze each repo with LLM
    4. Mark profitable repos
    5. Create deployment jobs
    """
    master_agent = get_master_agent()
    
    # Get in-progress registry
    in_progress = [
        job.repo_name for job in master_agent.jobs.values()
        if job.status in ["pending", "analyzing", "deploying"]
    ]
    
    # Scan and create jobs
    result = master_agent.scan_and_create_jobs(
        github_username=request.username,
        in_progress_registry=in_progress
    )
    
    return {
        "username": request.username,
        "total_repos": result["scan_result"].get("total_repos", 0),
        "active_repos": result["scan_result"].get("active_repos", 0),
        "profitable_count": result["total_profitable"],
        "created_jobs": result["created_jobs"],
        "queue_length": len(master_agent.job_queue)
    }


@app.get("/api/github/user/{username}/repos")
async def get_user_repos(username: str):
    """Get list of repositories for a GitHub user."""
    scanner = get_github_scanner()
    repos = scanner.scan_repositories(username)
    
    return {
        "username": username,
        "count": len(repos),
        "repos": [
            {
                "name": r.name,
                "url": r.html_url,
                "language": r.language,
                "stars": r.stars,
                "updated": r.updated_at.isoformat()
            }
            for r in repos
        ]
    }


# ============================================================================
# Job Management Endpoints
# ============================================================================

@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    """List all jobs, optionally filtered by status."""
    master_agent = get_master_agent()
    
    jobs = []
    for job_id, job in master_agent.jobs.items():
        if status and job.status != status:
            continue
        
        jobs.append(master_agent.get_job_status(job_id))
    
    return {
        "total": len(jobs),
        "jobs": jobs
    }


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get details of a specific job."""
    master_agent = get_master_agent()
    job = master_agent.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@app.post("/api/jobs/{job_id}/decide")
async def decide_job(job_id: str, request: JobDecisionRequest = None):
    """
    Run Master Agent decision on a job.
    
    The Master Agent uses a large GGUF model to decide:
    - proceed: Deploy the repo
    - skip: Not profitable enough
    - defer: Wait for better conditions
    - escalate: Needs human review
    """
    master_agent = get_master_agent()
    
    # Make decision
    decision = master_agent.decide_job(job_id)
    
    # Execute decision
    result = master_agent.execute_decision(decision)
    
    return {
        "job_id": job_id,
        "decision": {
            "action": decision.action,
            "reasoning": decision.reasoning,
            "priority": decision.priority,
            "assigned_agent": decision.assigned_agent
        },
        "result": result
    }


@app.post("/api/jobs/process-queue")
async def process_job_queue():
    """Process all jobs in queue."""
    master_agent = get_master_agent()
    results = master_agent.process_job_queue()
    
    return {
        "processed": len(results),
        "results": results,
        "queue_remaining": len(master_agent.job_queue)
    }


@app.get("/api/jobs/queue/status")
async def get_queue_status():
    """Get job queue status."""
    master_agent = get_master_agent()
    return master_agent.get_queue_status()


# ============================================================================
# Deployment Endpoints
# ============================================================================

@app.post("/api/deploy/start")
async def start_deployment(request: DeployRequest, background_tasks: BackgroundTasks):
    """
    Start deployment for a repository.
    
    Args:
        repo_name: Repository name
        repo_url: GitHub repository URL
        platform: Optional preferred platform
        project_type: Optional project type
    """
    # Create job
    master_agent = get_master_agent()
    
    from src.agents.master_agent import Job
    job = Job(
        id=str(uuid.uuid4()),
        repo_name=request.repo_name,
        repo_url=request.repo_url,
        status="pending",
        profitable=True,
        profit_score=7.0
    )
    
    master_agent.jobs[job.id] = job
    master_agent.job_queue.append(job.id)
    
    return {
        "job_id": job.id,
        "status": "queued",
        "repo_name": job.repo_name,
        "repo_url": job.repo_url
    }


@app.get("/api/deploy/{job_id}/status")
async def get_deployment_status(job_id: str):
    """Get deployment status."""
    master_agent = get_master_agent()
    job = master_agent.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


# ============================================================================
# Memory Endpoints
# ============================================================================

@app.get("/api/memory/summary")
async def get_memory_summary():
    """Get memory system summary."""
    memory_agent = get_memory_agent()
    return memory_agent.get_memory_summary()


@app.get("/api/memory/{repo_name}")
async def get_repo_memory(repo_name: str):
    """Get all memory for a specific repository."""
    memory_agent = get_memory_agent()
    return memory_agent.get_repo_memory(repo_name)


@app.get("/api/memory/drift/summary")
async def get_drift_summary(repo_name: Optional[str] = None):
    """Get drift tracking summary."""
    memory_agent = get_memory_agent()
    return memory_agent.get_drift_summary(repo_name)


@app.get("/api/memory/{repo_name}/should-process")
async def should_process_repo(repo_name: str, profit_score: float):
    """Check if repo should be processed based on memory."""
    memory_agent = get_memory_agent()
    return memory_agent.should_process_repo(repo_name, profit_score)


# ============================================================================
# Agent Status
# ============================================================================

@app.get("/api/agents/status")
async def get_agent_status():
    """Get status of all agents."""
    master = get_master_agent()
    memory = get_memory_agent()
    
    return {
        "master_agent": {
            "jobs_total": len(master.jobs),
            "jobs_pending": len(master.job_queue),
            "jobs_completed": len(master.completed_jobs),
            "max_concurrent": master.max_concurrent_jobs
        },
        "memory_agent": memory.get_memory_summary(),
        "system": {
            "initialized": system_initialized,
            "models_loaded": len(get_model_pool().loaded_models)
        }
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
