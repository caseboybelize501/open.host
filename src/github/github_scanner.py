"""
GitHub Repository Scanner

Scans GitHub user repositories and analyzes them for potential deployment jobs.

Features:
- Scan user's public repos (e.g., github.com/caseboybelize501)
- Compare against "in-progress" registry
- Detect tech stack, activity level, deployment readiness
- Mark repos as "profitable" based on criteria
"""

import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from github import Github, GithubException
from src.llm.llm_engine import get_llm, extract_json


@dataclass
class GitHubRepo:
    """Represents a GitHub repository."""
    name: str
    full_name: str
    html_url: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    open_issues: int
    default_branch: str
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    is_fork: bool
    is_archived: bool
    is_private: bool
    topics: List[str] = field(default_factory=list)
    has_pages: bool = False
    deployment_status: str = "unknown"  # unknown, pending, deployed, failed
    profitable: bool = False
    profit_score: float = 0.0
    in_progress: bool = False
    job_id: Optional[str] = None


@dataclass
class RepoAnalysis:
    """Analysis result for a repository."""
    repo_name: str
    tech_stack: List[str]
    framework: Optional[str]
    build_system: Optional[str]
    deployment_ready: bool
    estimated_complexity: str  # low, medium, high
    recommended_platform: Optional[str]
    risk_factors: List[str]
    profit_score: float
    profitable: bool
    reasoning: str


class GitHubScanner:
    """
    Scans GitHub repositories and identifies deployment opportunities.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub scanner.
        
        Args:
            github_token: Optional GitHub personal access token
        """
        self.token = github_token or os.getenv("GITHUB_TOKEN")
        self.github = None
        self.user = None
        self._connect()
        self.llm = get_llm()
    
    def _connect(self):
        """Connect to GitHub API."""
        try:
            if self.token:
                self.github = Github(self.token)
            else:
                self.github = Github()  # Unauthenticated (rate limited)
            
            # Test connection
            self.github.get_user().login
            print("Connected to GitHub API")
        except GithubException as e:
            print(f"GitHub connection failed: {e}")
            self.github = None
    
    def set_user(self, username: str) -> bool:
        """
        Set GitHub user to scan.
        
        Args:
            username: GitHub username (e.g., "caseboybelize501")
        
        Returns:
            True if user found
        """
        if not self.github:
            print("Not connected to GitHub")
            return False
        
        try:
            self.user = self.github.get_user(username)
            print(f"Found user: {self.user.login}")
            return True
        except GithubException as e:
            print(f"User not found: {username} - {e}")
            return False
    
    def scan_repositories(self, username: Optional[str] = None) -> List[GitHubRepo]:
        """
        Scan all repositories for a user.
        
        Args:
            username: Optional GitHub username (uses pre-set user if None)
        
        Returns:
            List of GitHubRepo objects
        """
        if username:
            if not self.set_user(username):
                return []
        
        if not self.user:
            print("No user set")
            return []
        
        repos = []
        try:
            for gh_repo in self.user.get_repos(type="all"):
                repo = GitHubRepo(
                    name=gh_repo.name,
                    full_name=gh_repo.full_name,
                    html_url=gh_repo.html_url,
                    description=gh_repo.description,
                    language=gh_repo.language,
                    stars=gh_repo.stargazers_count,
                    forks=gh_repo.forks_count,
                    open_issues=gh_repo.open_issues_count,
                    default_branch=gh_repo.default_branch,
                    created_at=gh_repo.created_at,
                    updated_at=gh_repo.updated_at,
                    pushed_at=gh_repo.pushed_at,
                    is_fork=gh_repo.fork,
                    is_archived=gh_repo.archived,
                    is_private=gh_repo.private,
                    topics=gh_repo.get_topics(),
                    has_pages=gh_repo.has_pages
                )
                repos.append(repo)
        except GithubException as e:
            print(f"Error scanning repos: {e}")
        
        print(f"Scanned {len(repos)} repositories")
        return repos
    
    def filter_active_repos(self, repos: List[GitHubRepo], 
                           min_stars: int = 0,
                           exclude_forks: bool = True,
                           exclude_archived: bool = True) -> List[GitHubRepo]:
        """
        Filter repositories by activity criteria.
        
        Args:
            repos: List of repos to filter
            min_stars: Minimum star count
            exclude_forks: Exclude forked repos
            exclude_archived: Exclude archived repos
        
        Returns:
            Filtered list
        """
        filtered = []
        for repo in repos:
            if exclude_forks and repo.is_fork:
                continue
            if exclude_archived and repo.is_archived:
                continue
            if repo.stars < min_stars:
                continue
            
            # Check recent activity (updated in last 6 months)
            six_months_ago = datetime.now() - timedelta(days=180)
            if repo.updated_at.replace(tzinfo=None) < six_months_ago:
                continue
            
            filtered.append(repo)
        
        return filtered
    
    def analyze_repo(self, repo: GitHubRepo) -> RepoAnalysis:
        """
        Analyze a repository using LLM.
        
        Args:
            repo: GitHubRepo to analyze
        
        Returns:
            RepoAnalysis with tech stack, recommendations, etc.
        """
        # Build context for LLM
        context = self._build_repo_context(repo)
        
        # Use LLM to analyze
        prompt = f"""Analyze this GitHub repository and provide deployment assessment.

Repository: {repo.full_name}
{context}

Provide analysis in JSON format:
{{
    "tech_stack": ["list", "of", "technologies"],
    "framework": "detected framework or null",
    "build_system": "build system or null",
    "deployment_ready": true/false,
    "estimated_complexity": "low/medium/high",
    "recommended_platform": "netlify/vercel/github_pages/render/null",
    "risk_factors": ["list", "of", "risks"],
    "profit_score": 0.0-10.0,
    "profitable": true/false,
    "reasoning": "brief explanation"
}}"""

        schema = {
            "type": "object",
            "properties": {
                "tech_stack": {"type": "array", "items": {"type": "string"}},
                "framework": {"type": "string"},
                "build_system": {"type": "string"},
                "deployment_ready": {"type": "boolean"},
                "estimated_complexity": {"type": "string", "enum": ["low", "medium", "high"]},
                "recommended_platform": {"type": "string"},
                "risk_factors": {"type": "array", "items": {"type": "string"}},
                "profit_score": {"type": "number", "minimum": 0, "maximum": 10},
                "profitable": {"type": "boolean"},
                "reasoning": {"type": "string"}
            },
            "required": ["tech_stack", "deployment_ready", "profitable", "reasoning"]
        }

        result = extract_json(prompt, schema)
        
        if not result:
            # Fallback analysis
            return self._fallback_analysis(repo)
        
        return RepoAnalysis(
            repo_name=repo.full_name,
            tech_stack=result.get("tech_stack", []),
            framework=result.get("framework"),
            build_system=result.get("build_system"),
            deployment_ready=result.get("deployment_ready", False),
            estimated_complexity=result.get("estimated_complexity", "medium"),
            recommended_platform=result.get("recommended_platform"),
            risk_factors=result.get("risk_factors", []),
            profit_score=result.get("profit_score", 0.0),
            profitable=result.get("profitable", False),
            reasoning=result.get("reasoning", "")
        )
    
    def _build_repo_context(self, repo: GitHubRepo) -> str:
        """Build context string for LLM analysis."""
        context_parts = [
            f"Description: {repo.description or 'No description'}",
            f"Primary Language: {repo.language or 'Unknown'}",
            f"Stars: {repo.stars}",
            f"Forks: {repo.forks}",
            f"Open Issues: {repo.open_issues}",
            f"Topics: {', '.join(repo.topics) if repo.topics else 'None'}",
            f"Has Pages: {repo.has_pages}",
            f"Last Updated: {repo.updated_at.strftime('%Y-%m-%d')}",
            f"Is Fork: {repo.is_fork}",
            f"Is Archived: {repo.is_archived}",
        ]
        return "\n".join(context_parts)
    
    def _fallback_analysis(self, repo: GitHubRepo) -> RepoAnalysis:
        """Fallback analysis without LLM."""
        # Simple rule-based analysis
        tech_stack = []
        recommended_platform = None
        profitable = False
        profit_score = 0.0
        
        if repo.language:
            tech_stack.append(repo.language)
        
        # Platform recommendation based on language
        if repo.language in ["JavaScript", "TypeScript"]:
            recommended_platform = "vercel"
            profit_score += 3.0
        elif repo.language == "Python":
            recommended_platform = "render"
            profit_score += 2.0
        elif repo.language in ["HTML", "CSS"]:
            recommended_platform = "github_pages"
            profit_score += 1.0
        
        # Bonus for stars
        if repo.stars > 100:
            profit_score += 2.0
            profitable = True
        elif repo.stars > 10:
            profit_score += 1.0
        
        # Bonus for recent activity
        days_since_update = (datetime.now() - repo.updated_at.replace(tzinfo=None)).days
        if days_since_update < 30:
            profit_score += 2.0
        elif days_since_update < 90:
            profit_score += 1.0
        
        # Check if has pages (already deployed)
        if repo.has_pages:
            profit_score += 1.0
        
        profitable = profitable or profit_score >= 5.0
        
        return RepoAnalysis(
            repo_name=repo.full_name,
            tech_stack=tech_stack,
            framework=None,
            build_system=None,
            deployment_ready=repo.language is not None,
            estimated_complexity="medium",
            recommended_platform=recommended_platform,
            risk_factors=[],
            profit_score=profit_score,
            profitable=profitable,
            reasoning=f"Rule-based analysis: language={repo.language}, stars={repo.stars}, updated={days_since_update}d ago"
        )
    
    def check_repo_files(self, repo: GitHubRepo) -> Dict[str, bool]:
        """
        Check for key files in repository.
        
        Args:
            repo: GitHubRepo to check
        
        Returns:
            Dict of file presence flags
        """
        if not self.github:
            return {}
        
        try:
            gh_repo = self.github.get_repo(repo.full_name)
            
            # Check for key files
            key_files = {
                "package.json": False,
                "requirements.txt": False,
                "Dockerfile": False,
                "docker-compose.yml": False,
                "Cargo.toml": False,
                "go.mod": False,
                "index.html": False,
                "README.md": False,
                ".github/workflows": False,
            }
            
            contents = gh_repo.get_contents("")
            for item in contents:
                if item.path in key_files:
                    key_files[item.path] = True
                elif item.path.startswith(".github/workflows"):
                    key_files[".github/workflows"] = True
            
            return key_files
            
        except GithubException:
            return {}
    
    def get_repo_readme(self, repo_full_name: str) -> Optional[str]:
        """Get repository README content."""
        if not self.github:
            return None
        
        try:
            gh_repo = self.github.get_repo(repo_full_name)
            readme = gh_repo.get_readme()
            import base64
            return base64.b64decode(readme.content).decode('utf-8')
        except GithubException:
            return None
    
    def scan_user_for_jobs(self, username: str, 
                          in_progress_registry: List[str]) -> Dict:
        """
        Complete scan workflow: find repos not in progress and mark profitable ones.
        
        Args:
            username: GitHub username
            in_progress_registry: List of repo names already being processed
        
        Returns:
            Scan result with new job candidates
        """
        # Scan all repos
        repos = self.scan_repositories(username)
        
        # Filter active repos
        active_repos = self.filter_active_repos(repos)
        
        # Filter out in-progress repos
        new_candidates = [
            r for r in active_repos 
            if r.name not in in_progress_registry and not r.in_progress
        ]
        
        # Analyze each candidate
        analyzed = []
        profitable_repos = []
        
        for repo in new_candidates:
            analysis = self.analyze_repo(repo)
            analyzed.append({
                "repo": repo,
                "analysis": analysis
            })
            
            if analysis.profitable:
                profitable_repos.append({
                    "repo": repo,
                    "analysis": analysis
                })
        
        return {
            "username": username,
            "total_repos": len(repos),
            "active_repos": len(active_repos),
            "new_candidates": len(new_candidates),
            "profitable_count": len(profitable_repos),
            "profitable_repos": profitable_repos,
            "analyzed_repos": analyzed
        }


# Global scanner instance
_github_scanner: Optional[GitHubScanner] = None


def get_github_scanner(token: Optional[str] = None) -> GitHubScanner:
    """Get global GitHub scanner instance."""
    global _github_scanner
    if _github_scanner is None:
        _github_scanner = GitHubScanner(token)
    return _github_scanner


def scan_github_user(username: str) -> List[GitHubRepo]:
    """Convenience function to scan a GitHub user."""
    scanner = get_github_scanner()
    return scanner.scan_repositories(username)


def analyze_github_repo(repo: GitHubRepo) -> RepoAnalysis:
    """Convenience function to analyze a repo."""
    scanner = get_github_scanner()
    return scanner.analyze_repo(repo)
