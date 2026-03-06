"""
Shared Pydantic models for Open.Host Jarvis.

These models are used across the application for:
- API request/response validation
- Data transfer between components
- Configuration management
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


# ============================================================================
# Deployment Models
# ============================================================================

class DeploymentRequest(BaseModel):
    """Request to start a deployment."""
    project_path: str = Field(..., description="Path to project directory")
    description: Optional[str] = Field(None, description="Optional project description")
    platform: Optional[str] = Field(None, description="Preferred platform")


class DeploymentResponse(BaseModel):
    """Response from deployment request."""
    deployment_id: str
    status: str
    url: Optional[str] = None
    platform: Optional[str] = None
    validation_passed: bool = False
    error: Optional[str] = None


class DeploymentStatus(BaseModel):
    """Current status of a deployment."""
    id: str
    project_path: str
    project_type: Optional[str] = None
    platform: Optional[str] = None
    status: str  # deploying, deployed, failed
    url: Optional[str] = None
    stages: List[Dict] = []
    consecutive_passes: int = 0
    stable: bool = False
    created_at: Optional[float] = None
    updated_at: Optional[float] = None


# ============================================================================
# Validation Models
# ============================================================================

class ValidationStage(BaseModel):
    """Single validation stage result."""
    stage: int
    name: str
    description: str
    passed: bool
    timestamp: float
    error: Optional[str] = None
    mutation_test: Optional[Dict] = None


class ValidationResult(BaseModel):
    """Complete validation cycle result."""
    deployment_id: Optional[str] = None
    cycle: int
    stages: List[ValidationStage]
    overall_pass: bool
    consecutive_passes: int
    stable: bool
    stages_passed: int
    total_stages: int


class ValidationSummary(BaseModel):
    """Summary of validation state."""
    current_cycle: int
    consecutive_passes: int
    required_for_stable: int = 7
    stable_designs: int
    last_failure_stage: Optional[int] = None
    progress_to_stable: str


# ============================================================================
# Memory Models
# ============================================================================

class FailureRecord(BaseModel):
    """Record of a deployment failure."""
    project_type: str
    platform: str
    build_command: str
    error_message: str
    failure_stage: int
    fix_applied: str
    cycles_to_stable: int


class BuildStrategy(BaseModel):
    """Build strategy from memory library."""
    build_command: str
    env_vars: Dict[str, str]
    success: bool
    performance_score: float
    timestamp: Optional[float] = None


class PlatformRecommendation(BaseModel):
    """Platform recommendation from memory."""
    platform: Optional[str] = None
    confidence: float = 0.5
    avoid_platforms: List[str] = []
    suggested_build_command: Optional[str] = None
    predicted_cycles_to_stable: int = 3
    notes: str = ""


class MemorySummary(BaseModel):
    """Summary of memory system state."""
    total_failures: int
    total_strategies: int
    total_patterns: int
    training_data_points: int
    model_trained: bool


# ============================================================================
# System Profile Models
# ============================================================================

class ToolInfo(BaseModel):
    """Information about a detected tool."""
    name: str
    version: str
    path: Optional[str] = None
    available: bool = True


class PlatformInfo(BaseModel):
    """Information about a hosting platform."""
    name: str
    display_name: str
    healthy: bool = True
    supported_types: List[str] = []
    features: List[str] = []
    free_tier: Dict[str, str] = {}
    response_time_ms: Optional[int] = None


class SystemCapabilities(BaseModel):
    """System capability flags."""
    node_deploy: bool = False
    python_deploy: bool = False
    docker_deploy: bool = False
    netlify_deploy: bool = False
    vercel_deploy: bool = False
    github_pages_deploy: bool = False
    render_deploy: bool = False
    llm_inference: bool = False


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    tools_detected: int = 0
    platforms_available: int = 0
    consecutive_passes: int = 0
    memory_hit_rate: float = 0.0
    deployments_count: int = 0
    stable_designs: int = 0


# ============================================================================
# Project Models
# ============================================================================

class ProjectInfo(BaseModel):
    """Information about a project."""
    project_type: Optional[str] = None
    framework: Optional[str] = None
    build_command: Optional[str] = None
    output_dir: Optional[str] = None
    environment_vars: List[str] = []
    dependencies: List[str] = []
    platform_hints: List[str] = []
    source_dir: str = ""
    error: Optional[str] = None


class DeploymentPlan(BaseModel):
    """Deployment plan for a project."""
    project: ProjectInfo
    platforms: List[Dict]
    credentials: Dict[str, str]
    memory_recommendation: Optional[PlatformRecommendation] = None
    recommended_platform: Optional[Dict] = None
    plan_metadata: Dict[str, Any] = {}


# ============================================================================
# API Response Models
# ============================================================================

class APIResponse(BaseModel):
    """Generic API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated API response."""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False
