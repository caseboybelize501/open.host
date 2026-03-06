from typing import Dict, List, Optional
from src.memory.deployment_failure_store import failure_store, store_failure as store_failure_fn
from src.memory.project_pattern_graph import pattern_graph, update_project_pattern as update_pattern_fn
from src.memory.platform_library import library, update_build_strategy as update_strategy_fn
from src.memory.meta_learner import meta_learner, update_meta_learning as update_meta_fn
from src.agents.project_agent import analyze_project


class LearnAgent:
    """
    Autonomous learning agent with 4-layer memory system.
    
    Layer 1: Deployment Failure Store (ChromaDB-compatible)
      - Stores failure patterns per project type + platform
      - Query: "what fails for [React] on [Netlify]?"
    
    Layer 2: Project Pattern Graph (Neo4j)
      - Graph of project types → platform success relationships
      - Query: "which platforms work for [Next.js]?"
    
    Layer 3: Build Strategy Library
      - Effective build configurations per project type + platform
      - Query: "what build command works for [Vue] on [Vercel]?"
    
    Layer 4: Meta-Learning Index (sklearn)
      - Predicts cycles-to-stable based on approach
      - Query: "how many cycles for this project type?"
    """
    
    def __init__(self):
        self.recommendation_cache: Dict[str, Dict] = {}
        self.learning_events: List[Dict] = []
    
    def analyze_project(self, project_path: str) -> Dict:
        """Analyze project and enrich with memory recommendations."""
        project_info = analyze_project(project_path)
        project_type = project_info.get("project_type", "unknown")
        
        # Enrich with memory-based recommendations
        project_info["memory_recommendation"] = self.get_recommendation(project_type)
        project_info["predicted_cycles"] = self._predict_cycles_to_stable(project_type)
        project_info["avoid_platforms"] = self._get_platforms_to_avoid(project_type)
        
        return project_info
    
    def learn_from_deployment(self, project_type: str, platform: str, build_command: str,
                             error_message: Optional[str] = None, failure_stage: Optional[int] = None,
                             fix_applied: Optional[str] = None, cycles_to_stable: int = 1):
        """
        Learn from a deployment outcome (success or failure).
        
        Updates all 4 memory layers:
        1. Store failure pattern (if failed)
        2. Update project-platform graph
        3. Update build strategy library
        4. Update meta-learning index
        """
        # Layer 1: Store failure (if applicable)
        if error_message and failure_stage is not None:
            store_failure_fn(
                project_type=project_type,
                platform=platform,
                build_command=build_command,
                error_message=error_message,
                failure_stage=failure_stage,
                fix_applied=fix_applied or "unknown",
                cycles_to_stable=cycles_to_stable
            )
        
        # Layer 2: Update project pattern graph
        outcome = "failure" if error_message else "success"
        update_pattern_fn(project_type, platform, outcome, failure_stage or 0)
        
        # Layer 3: Update build strategy library
        update_strategy_fn(
            project_type=project_type,
            platform=platform,
            build_command=build_command,
            env_vars={},
            success=(error_message is None),
            performance_score=0.0 if error_message else 1.0
        )
        
        # Layer 4: Update meta-learning index
        approach = self._determine_approach(project_type, platform, error_message)
        update_meta_fn(project_type, approach, cycles_to_stable)
        
        # Record learning event
        self.learning_events.append({
            "project_type": project_type,
            "platform": platform,
            "outcome": outcome,
            "cycles_to_stable": cycles_to_stable,
            "timestamp": self._get_timestamp()
        })
    
    def learn_from_success(self, project_type: str, platform: str, build_command: str,
                          cycles_to_stable: int):
        """Learn from a successful deployment."""
        self.learn_from_deployment(
            project_type=project_type,
            platform=platform,
            build_command=build_command,
            error_message=None,
            failure_stage=None,
            fix_applied=None,
            cycles_to_stable=cycles_to_stable
        )
    
    def get_recommendation(self, project_type: str) -> Dict:
        """
        Get platform recommendation for project type.
        
        Queries all 4 memory layers to provide best recommendation.
        """
        # Check cache first
        if project_type in self.recommendation_cache:
            return self.recommendation_cache[project_type]
        
        # Layer 3: Get best build strategy
        best_strategy = None
        best_platform = None
        best_score = -1
        
        # Check all known platforms
        known_platforms = ["netlify", "vercel", "github_pages", "render"]
        for platform in known_platforms:
            strategy = library.get_best_strategy(project_type, platform)
            if strategy and strategy.get("success"):
                score = strategy.get("performance_score", 0.5)
                if score > best_score:
                    best_score = score
                    best_strategy = strategy
                    best_platform = platform
        
        # Layer 1: Check for platforms to avoid
        failures = failure_store.get_failures_for_project_type(project_type)
        avoid_platforms = list(set(f["platform"] for f in failures if f.get("failure_stage") == 3))
        
        # Layer 2: Get pattern graph insights (if available)
        pattern_insights = self._get_pattern_insights(project_type)
        
        # Layer 4: Get meta-learning prediction
        predicted_cycles = self._predict_cycles_to_stable(project_type)
        
        recommendation = {
            "platform": best_platform,
            "confidence": best_score if best_score > 0 else 0.5,
            "avoid_platforms": avoid_platforms,
            "suggested_build_command": best_strategy.get("build_command") if best_strategy else None,
            "pattern_insights": pattern_insights,
            "predicted_cycles_to_stable": predicted_cycles,
            "notes": self._generate_recommendation_notes(best_platform, avoid_platforms, best_score)
        }
        
        # Cache recommendation
        self.recommendation_cache[project_type] = recommendation
        
        return recommendation
    
    def _get_pattern_insights(self, project_type: str) -> Dict:
        """Get insights from project pattern graph (Layer 2)."""
        # Placeholder - would query Neo4j
        return {
            "success_count": 0,
            "failure_count": len(failure_store.get_failures_for_project_type(project_type)),
            "common_platforms": []
        }
    
    def _predict_cycles_to_stable(self, project_type: str) -> int:
        """Predict cycles to stable using meta-learner (Layer 4)."""
        # Default prediction if model not trained
        if len(meta_learner.training_data) < 5:
            return 3  # Default estimate
        
        return meta_learner.predict_cycles(project_type, "memory_guided")
    
    def _get_platforms_to_avoid(self, project_type: str) -> List[str]:
        """Get list of platforms to avoid for project type."""
        failures = failure_store.get_failures_for_project_type(project_type)
        return list(set(f["platform"] for f in failures if f.get("failure_stage") == 3))
    
    def _determine_approach(self, project_type: str, platform: str, error_message: Optional[str]) -> str:
        """Determine which approach was used for meta-learning."""
        if error_message:
            return "naive"
        
        # Check if memory was used
        if project_type in self.recommendation_cache:
            return "memory_guided"
        
        return "platform_tuned"
    
    def _generate_recommendation_notes(self, platform: Optional[str], 
                                       avoid_platforms: List[str], score: float) -> str:
        """Generate human-readable recommendation notes."""
        notes = []
        
        if platform:
            notes.append(f"Recommended: {platform}")
        else:
            notes.append("No historical data - trying default platform")
        
        if avoid_platforms:
            notes.append(f"Avoid: {', '.join(avoid_platforms)}")
        
        if score > 0.8:
            notes.append("High confidence based on historical success")
        elif score > 0.5:
            notes.append("Moderate confidence")
        else:
            notes.append("Low confidence - limited historical data")
        
        return "; ".join(notes)
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def get_learning_summary(self) -> Dict:
        """Get summary of all learning events."""
        return {
            "total_events": len(self.learning_events),
            "recent_events": self.learning_events[-10:],
            "unique_project_types": len(set(e["project_type"] for e in self.learning_events)),
            "unique_platforms": len(set(e["platform"] for e in self.learning_events))
        }


# Global instance
learn_agent = LearnAgent()
