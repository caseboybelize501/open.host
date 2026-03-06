"""
Memory Agent - Drift and State Manager

Manages the 4-layer memory system with added drift tracking:
1. Deployment Failure Store (ChromaDB)
2. Project Pattern Graph (Neo4j)
3. Build Strategy Library
4. Meta-Learning Index (sklearn)

Plus drift tracking for:
- Repo state changes over time
- Profitability drift
- Configuration drift
- Job completion patterns
"""

import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from src.memory.deployment_failure_store import failure_store, store_failure
from src.memory.project_pattern_graph import pattern_graph, update_project_pattern
from src.memory.platform_library import library, update_build_strategy
from src.memory.meta_learner import meta_learner, update_meta_learning


@dataclass
class DriftRecord:
    """Records state drift for a repository."""
    repo_name: str
    timestamp: float
    drift_type: str  # profitability, state, config, activity
    previous_value: Any
    current_value: Any
    drift_magnitude: float  # 0-1
    significant: bool = False


@dataclass
class RepoState:
    """Current state of a repository."""
    repo_name: str
    last_scan: float
    profitable: bool
    profit_score: float
    deployment_status: str
    last_commit: Optional[datetime]
    last_push: Optional[datetime]
    open_issues: int
    stars: int
    config_hash: str
    drift_records: List[DriftRecord] = field(default_factory=list)
    profitability_history: List[Dict] = field(default_factory=list)


class MemoryAgent:
    """
    Memory Agent managing 4-layer memory + drift tracking.
    
    Responsibilities:
    - Store and retrieve from all 4 memory layers
    - Track repo state drift over time
    - Detect significant profitability changes
    - Mark repos as "profitable" based on patterns
    - Provide historical context for decisions
    """
    
    def __init__(self):
        self.repo_states: Dict[str, RepoState] = {}
        self.drift_threshold = 0.3  # Threshold for significant drift
        self.profitability_window = 30  # Days to consider for profitability
        
    def record_job_outcome(self, job_id: str, repo_name: str, 
                          project_type: str, platform: str,
                          success: bool, error_message: Optional[str] = None,
                          build_command: str = "", cycles_to_stable: int = 1):
        """
        Record job outcome to all 4 memory layers.
        
        Args:
            job_id: Job identifier
            repo_name: Repository name
            project_type: Type of project
            platform: Platform deployed to
            success: Whether deployment succeeded
            error_message: Error if failed
            build_command: Build command used
            cycles_to_stable: Cycles to reach stable
        """
        timestamp = time.time()
        
        # Layer 1: Failure Store
        if not success and error_message:
            store_failure(
                project_type=project_type,
                platform=platform,
                build_command=build_command,
                error_message=error_message,
                failure_stage=3,  # Deploy stage
                fix_applied="none",
                cycles_to_stable=cycles_to_stable
            )
        
        # Layer 2: Pattern Graph
        outcome = "success" if success else "failure"
        update_project_pattern(project_type, platform, outcome, 3)
        
        # Layer 3: Build Strategy Library
        update_build_strategy(
            project_type=project_type,
            platform=platform,
            build_command=build_command,
            env_vars={},
            success=success,
            performance_score=1.0 if success else 0.0
        )
        
        # Layer 4: Meta-Learning
        approach = "memory_guided" if success else "naive"
        update_meta_learning(project_type, approach, cycles_to_stable)
        
        # Update repo state
        self._update_repo_state(repo_name, success, timestamp)
    
    def _update_repo_state(self, repo_name: str, success: bool, timestamp: float):
        """Update repository state after job."""
        if repo_name not in self.repo_states:
            self.repo_states[repo_name] = RepoState(
                repo_name=repo_name,
                last_scan=timestamp,
                profitable=success,
                profit_score=5.0 if success else 2.0,
                deployment_status="deployed" if success else "failed",
                last_commit=None,
                last_push=None,
                open_issues=0,
                stars=0,
                config_hash=""
            )
        
        state = self.repo_states[repo_name]
        state.last_scan = timestamp
        state.deployment_status = "deployed" if success else "failed"
        
        # Update profitability
        if success:
            state.profit_score = min(10.0, state.profit_score + 1.0)
            state.profitable = state.profit_score >= 5.0
        else:
            state.profit_score = max(0.0, state.profit_score - 2.0)
            state.profitable = state.profit_score >= 5.0
        
        # Record profitability history
        state.profitability_history.append({
            "timestamp": timestamp,
            "profit_score": state.profit_score,
            "profitable": state.profitable,
            "outcome": "success" if success else "failure"
        })
        
        # Keep only last 100 entries
        if len(state.profitability_history) > 100:
            state.profitability_history = state.profitability_history[-100:]
    
    def check_drift(self, repo_name: str, 
                   current_profit_score: float,
                   current_state: str) -> Optional[DriftRecord]:
        """
        Check for significant drift in repo state.
        
        Args:
            repo_name: Repository name
            current_profit_score: Current profit score
            current_state: Current deployment status
        
        Returns:
            DriftRecord if significant drift detected
        """
        if repo_name not in self.repo_states:
            return None
        
        state = self.repo_states[repo_name]
        
        # Check profitability drift
        profit_diff = abs(current_profit_score - state.profit_score) / 10.0
        
        if profit_diff > self.drift_threshold:
            drift = DriftRecord(
                repo_name=repo_name,
                timestamp=time.time(),
                drift_type="profitability",
                previous_value=state.profit_score,
                current_value=current_profit_score,
                drift_magnitude=profit_diff,
                significant=True
            )
            state.drift_records.append(drift)
            return drift
        
        # Check state drift
        if current_state != state.deployment_status:
            drift = DriftRecord(
                repo_name=repo_name,
                timestamp=time.time(),
                drift_type="state",
                previous_value=state.deployment_status,
                current_value=current_state,
                drift_magnitude=0.5,
                significant=True
            )
            state.drift_records.append(drift)
            return drift
        
        return None
    
    def get_repo_memory(self, repo_name: str) -> Dict:
        """
        Get all memory for a repository.
        
        Args:
            repo_name: Repository name
        
        Returns:
            Dict with all memory layers + drift
        """
        # Get failure history
        failures = failure_store.get_failures_for_project_type(repo_name)
        
        # Get pattern graph data
        patterns = pattern_graph.get_patterns_for_project_type(repo_name)
        
        # Get build strategies
        strategies = library.get_all_strategies(project_type=repo_name)
        
        # Get repo state
        state = self.repo_states.get(repo_name)
        
        return {
            "repo_name": repo_name,
            "state": {
                "profitable": state.profitable if state else False,
                "profit_score": state.profit_score if state else 5.0,
                "deployment_status": state.deployment_status if state else "unknown"
            },
            "failures": len(failures),
            "patterns": len(patterns),
            "strategies": len(strategies),
            "drift_count": len(state.drift_records) if state else 0,
            "profitability_trend": self._calculate_profitability_trend(state) if state else "stable"
        }
    
    def _calculate_profitability_trend(self, state: RepoState) -> str:
        """Calculate profitability trend from history."""
        history = state.profitability_history
        if len(history) < 2:
            return "stable"
        
        recent = history[-5:]
        scores = [h["profit_score"] for h in recent]
        
        if len(scores) < 2:
            return "stable"
        
        avg_first = sum(scores[:len(scores)//2]) / (len(scores)//2)
        avg_second = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        if avg_second > avg_first + 1.0:
            return "improving"
        elif avg_second < avg_first - 1.0:
            return "declining"
        else:
            return "stable"
    
    def should_process_repo(self, repo_name: str, 
                           profit_score: float) -> Dict:
        """
        Decide if repo should be processed based on memory.
        
        Args:
            repo_name: Repository name
            profit_score: Current profit score
        
        Returns:
            Decision dict with reasoning
        """
        memory = self.get_repo_memory(repo_name)
        state = memory.get("state", {})
        
        # Check if previously profitable
        was_profitable = state.get("profitable", False)
        current_profitable = profit_score >= 5.0
        
        # Check trend
        trend = memory.get("profitability_trend", "stable")
        
        # Check failure history
        failure_count = memory.get("failures", 0)
        
        # Decision logic
        should_process = True
        reasons = []
        
        if not current_profitable:
            should_process = False
            reasons.append("Not profitable")
        
        if trend == "declining":
            should_process = False
            reasons.append("Declining profitability trend")
        
        if failure_count > 3:
            should_process = False
            reasons.append(f"High failure count: {failure_count}")
        
        if was_profitable and not current_profitable:
            reasons.append("Profitability dropped")
        
        return {
            "should_process": should_process,
            "reasons": reasons,
            "memory": memory
        }
    
    def mark_repo_profitable(self, repo_name: str, 
                            profit_score: float,
                            reason: str = ""):
        """
        Explicitly mark a repo as profitable.
        
        Args:
            repo_name: Repository name
            profit_score: Profit score
            reason: Reason for marking profitable
        """
        timestamp = time.time()
        
        if repo_name not in self.repo_states:
            self.repo_states[repo_name] = RepoState(
                repo_name=repo_name,
                last_scan=timestamp,
                profitable=True,
                profit_score=profit_score,
                deployment_status="pending",
                last_commit=None,
                last_push=None,
                open_issues=0,
                stars=0,
                config_hash=""
            )
        else:
            state = self.repo_states[repo_name]
            state.profitable = True
            state.profit_score = profit_score
            state.last_scan = timestamp
        
        # Record in profitability history
        self.repo_states[repo_name].profitability_history.append({
            "timestamp": timestamp,
            "profit_score": profit_score,
            "profitable": True,
            "reason": reason,
            "marked": True
        })
    
    def get_drift_summary(self, repo_name: Optional[str] = None) -> Dict:
        """
        Get drift summary.
        
        Args:
            repo_name: Optional specific repo
        
        Returns:
            Drift summary dict
        """
        if repo_name:
            state = self.repo_states.get(repo_name)
            if not state:
                return {"repo": repo_name, "drifts": []}
            
            return {
                "repo": repo_name,
                "drifts": [
                    {
                        "type": d.drift_type,
                        "magnitude": d.drift_magnitude,
                        "timestamp": datetime.fromtimestamp(d.timestamp).isoformat(),
                        "significant": d.significant
                    }
                    for d in state.drift_records
                ]
            }
        
        # All repos
        all_drifts = []
        for name, state in self.repo_states.items():
            for drift in state.drift_records:
                all_drifts.append({
                    "repo": name,
                    "type": drift.drift_type,
                    "magnitude": drift.drift_magnitude,
                    "timestamp": datetime.fromtimestamp(drift.timestamp).isoformat()
                })
        
        return {
            "total_repos": len(self.repo_states),
            "total_drifts": len(all_drifts),
            "significant_drifts": sum(1 for d in all_drifts if d.get("significant", False)),
            "recent_drifts": all_drifts[-20:]
        }
    
    def get_memory_summary(self) -> Dict:
        """Get summary of all memory layers."""
        return {
            "repo_states": len(self.repo_states),
            "failure_store_size": len(failure_store.failures),
            "pattern_graph_size": len(pattern_graph.get_all_patterns()),
            "strategy_library_size": len(library.build_strategies),
            "meta_learning_samples": len(meta_learner.training_data),
            "drift_records": sum(len(s.drift_records) for s in self.repo_states.values())
        }


# Global memory agent instance
_memory_agent: Optional[MemoryAgent] = None


def get_memory_agent() -> MemoryAgent:
    """Get global Memory Agent instance."""
    global _memory_agent
    if _memory_agent is None:
        _memory_agent = MemoryAgent()
    return _memory_agent
