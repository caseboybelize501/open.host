"""
Analyzer Agent - Specialized Small Model

Uses smaller GGUF model (1-3B) for:
- Code analysis and tech stack detection
- Repository structure analysis
- Risk assessment
- Complexity estimation

Faster and cheaper than master model for routine analysis tasks.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.llm.llm_engine import get_llm, extract_json, classify
from src.github.github_scanner import GitHubRepo, RepoAnalysis


@dataclass
class AnalysisResult:
    """Result from analyzer agent."""
    job_id: str
    success: bool
    tech_stack: List[str]
    framework: Optional[str]
    build_system: Optional[str]
    file_structure: Dict[str, bool]
    complexity_score: float  # 0-10
    risk_score: float  # 0-10
    deployment_confidence: float  # 0-1
    recommendations: List[str]
    warnings: List[str]
    error: Optional[str] = None


class AnalyzerAgent:
    """
    Analyzer Agent using small GGUF model.
    
    Specialized for code analysis tasks that don't require
    the master model's full reasoning capability.
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.analysis_cache: Dict[str, AnalysisResult] = {}
    
    def analyze_repo_job(self, job) -> Dict:
        """
        Analyze a repository job.
        
        Args:
            job: Job object from Master Agent
        
        Returns:
            Analysis result dict
        """
        job_id = job.id
        repo_name = job.repo_name
        analysis = job.analysis
        
        # Check cache
        if job_id in self.analysis_cache:
            return {
                "success": True,
                "cached": True,
                "result": self.analysis_cache[job_id]
            }
        
        # Perform analysis
        result = self._analyze_repository(repo_name, analysis)
        
        # Cache result
        self.analysis_cache[job_id] = result
        
        # Update job
        job.status = "analyzed"
        job.result = {
            "tech_stack": result.tech_stack,
            "framework": result.framework,
            "complexity_score": result.complexity_score,
            "risk_score": result.risk_score,
            "deployment_confidence": result.deployment_confidence
        }
        
        return {
            "success": True,
            "job_id": job_id,
            "analysis": result
        }
    
    def _analyze_repository(self, repo_name: str, 
                           analysis: Optional[RepoAnalysis]) -> AnalysisResult:
        """
        Perform detailed repository analysis.
        
        Args:
            repo_name: Repository name
            analysis: Existing analysis from scanner
        
        Returns:
            AnalysisResult
        """
        tech_stack = analysis.tech_stack if analysis else []
        framework = analysis.framework
        build_system = analysis.build_system
        
        # Use LLM to refine analysis if we have more context
        if analysis and analysis.reasoning:
            refined = self._refine_analysis(repo_name, analysis)
            if refined:
                tech_stack = refined.get("tech_stack", tech_stack)
                framework = refined.get("framework", framework)
                build_system = refined.get("build_system", build_system)
        
        # Calculate scores
        complexity_score = self._calculate_complexity(analysis)
        risk_score = self._calculate_risk(analysis)
        deployment_confidence = self._calculate_confidence(analysis)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analysis)
        warnings = self._generate_warnings(analysis)
        
        return AnalysisResult(
            job_id="",
            success=True,
            tech_stack=tech_stack,
            framework=framework,
            build_system=build_system,
            file_structure={},  # Would be populated with file analysis
            complexity_score=complexity_score,
            risk_score=risk_score,
            deployment_confidence=deployment_confidence,
            recommendations=recommendations,
            warnings=warnings
        )
    
    def _refine_analysis(self, repo_name: str, analysis: RepoAnalysis) -> Optional[Dict]:
        """Use LLM to refine existing analysis."""
        prompt = f"""Refine this repository analysis.

Repository: {repo_name}
Current Analysis:
- Tech Stack: {', '.join(analysis.tech_stack)}
- Framework: {analysis.framework or 'Unknown'}
- Build System: {analysis.build_system or 'Unknown'}
- Reasoning: {analysis.reasoning}

Provide refined analysis as JSON:
{{
    "tech_stack": ["more", "specific", "technologies"],
    "framework": "specific framework",
    "build_system": "specific build system"
}}"""

        schema = {
            "type": "object",
            "properties": {
                "tech_stack": {"type": "array", "items": {"type": "string"}},
                "framework": {"type": "string"},
                "build_system": {"type": "string"}
            }
        }

        return extract_json(prompt, schema, temperature=0.3)
    
    def _calculate_complexity(self, analysis: Optional[RepoAnalysis]) -> float:
        """Calculate complexity score 0-10."""
        if not analysis:
            return 5.0
        
        score = 5.0
        
        # Complexity based on tech stack size
        if len(analysis.tech_stack) > 5:
            score += 2.0
        elif len(analysis.tech_stack) > 2:
            score += 1.0
        
        # Complexity based on estimated level
        complexity_map = {"low": -2.0, "medium": 0.0, "high": 2.0}
        score += complexity_map.get(analysis.estimated_complexity, 0.0)
        
        # Risk factors add complexity
        score += len(analysis.risk_factors) * 0.5
        
        return max(0.0, min(10.0, score))
    
    def _calculate_risk(self, analysis: Optional[RepoAnalysis]) -> float:
        """Calculate risk score 0-10."""
        if not analysis:
            return 5.0
        
        score = 3.0  # Base risk
        
        # Risk factors
        score += len(analysis.risk_factors) * 1.5
        
        # Not deployment ready
        if not analysis.deployment_ready:
            score += 2.0
        
        # High complexity
        if analysis.estimated_complexity == "high":
            score += 1.5
        
        return max(0.0, min(10.0, score))
    
    def _calculate_confidence(self, analysis: Optional[RepoAnalysis]) -> float:
        """Calculate deployment confidence 0-1."""
        if not analysis:
            return 0.5
        
        confidence = 0.5
        
        # Has framework identified
        if analysis.framework:
            confidence += 0.2
        
        # Deployment ready
        if analysis.deployment_ready:
            confidence += 0.2
        
        # Low risk
        if len(analysis.risk_factors) == 0:
            confidence += 0.1
        
        # Has build system
        if analysis.build_system:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _generate_recommendations(self, analysis: Optional[RepoAnalysis]) -> List[str]:
        """Generate deployment recommendations."""
        recommendations = []
        
        if not analysis:
            return ["Perform initial analysis before deployment"]
        
        if not analysis.deployment_ready:
            recommendations.append("Add deployment configuration before proceeding")
        
        if analysis.recommended_platform:
            recommendations.append(f"Deploy to {analysis.recommended_platform} for optimal results")
        
        if analysis.framework == "Next.js":
            recommendations.append("Ensure Vercel is configured for Next.js features")
        elif analysis.framework == "React":
            recommendations.append("Configure build output directory for SPA hosting")
        
        if len(analysis.risk_factors) > 0:
            recommendations.append("Address risk factors before production deployment")
        
        return recommendations
    
    def _generate_warnings(self, analysis: Optional[RepoAnalysis]) -> List[str]:
        """Generate warnings."""
        warnings = []
        
        if not analysis:
            return warnings
        
        if analysis.estimated_complexity == "high":
            warnings.append("High complexity - expect longer deployment time")
        
        if len(analysis.risk_factors) > 2:
            warnings.append("Multiple risk factors detected - review before deploying")
        
        if analysis.profit_score < 5.0:
            warnings.append("Low profit score - verify deployment value")
        
        return warnings
    
    def classify_task(self, text: str, categories: List[str]) -> Optional[str]:
        """
        Classify text into category using small model.
        
        Fast classification for routine tasks.
        """
        return classify(text, categories, temperature=0.1)
    
    def extract_tech_stack(self, readme_content: str) -> List[str]:
        """
        Extract tech stack from README content.
        
        Args:
            readme_content: README markdown content
        
        Returns:
            List of detected technologies
        """
        prompt = f"""Extract all technologies, frameworks, and tools mentioned in this README.

{readme_content[:2000]}  # Limit context

Respond with JSON array of technology names: ["tech1", "tech2", ...]"""

        result = extract_json(prompt, {"type": "array", "items": {"type": "string"}})
        return result if result else []


# Global analyzer agent instance
_analyzer_agent: Optional[AnalyzerAgent] = None


def get_analyzer_agent() -> AnalyzerAgent:
    """Get global Analyzer Agent instance."""
    global _analyzer_agent
    if _analyzer_agent is None:
        _analyzer_agent = AnalyzerAgent()
    return _analyzer_agent
