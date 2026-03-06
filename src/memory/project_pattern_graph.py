from typing import Dict, List, Optional
import os


class ProjectPatternGraph:
    """
    Neo4j-backed graph of project types → platform success relationships.
    
    Stores and queries patterns like:
    - React projects succeed on Vercel
    - Next.js projects succeed on Netlify
    - Python projects fail on GitHub Pages
    
    When Neo4j is not available, falls back to in-memory storage.
    """
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, 
                 password: Optional[str] = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        # In-memory fallback
        self.in_memory: Dict[str, List[Dict]] = {
            "nodes": [],
            "relationships": []
        }
        
        # Try to connect to Neo4j
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Attempt to connect to Neo4j."""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            print(f"Neo4j connection failed: {e}. Using in-memory storage.")
            self.driver = None
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def update_project_pattern(self, project_type: str, platform: str, 
                              outcome: str, stage: int):
        """
        Update project-platform relationship based on outcome.
        
        Args:
            project_type: Type of project (react, vue, python, etc.)
            platform: Platform name (netlify, vercel, etc.)
            outcome: 'success' or 'failure'
            stage: Stage number where outcome occurred
        """
        if self.driver:
            self._update_neo4j(project_type, platform, outcome, stage)
        else:
            self._update_in_memory(project_type, platform, outcome, stage)
    
    def _update_neo4j(self, project_type: str, platform: str, 
                     outcome: str, stage: int):
        """Update pattern in Neo4j."""
        with self.driver.session() as session:
            session.write_transaction(
                self._create_project_pattern_tx,
                project_type, platform, outcome, stage
            )
    
    @staticmethod
    def _create_project_pattern_tx(tx, project_type: str, platform: str, 
                                   outcome: str, stage: int):
        """Neo4j transaction to create/update pattern."""
        # Create or merge project type node
        query = (
            "MERGE (p:ProjectType {name: $project_type}) "
            "MERGE (pl:Platform {name: $platform}) "
            f"{'MERGE (p)-[:SUCCEEDS_ON {stage: $stage, count: 1}]->(pl)' if outcome == 'success' else 'MERGE (p)-[:FAILS_ON {stage: $stage, count: 1}]->(pl)'} "
            "SET pl.last_used = timestamp()"
        )
        tx.run(query, project_type=project_type, platform=platform, stage=stage)
    
    def _update_in_memory(self, project_type: str, platform: str, 
                         outcome: str, stage: int):
        """Update pattern in in-memory storage."""
        relationship = {
            "project_type": project_type,
            "platform": platform,
            "outcome": outcome,
            "stage": stage,
            "timestamp": self._get_timestamp()
        }
        self.in_memory["relationships"].append(relationship)
    
    def get_all_patterns(self) -> List[Dict]:
        """Get all patterns from graph."""
        if self.driver:
            return self._get_patterns_neo4j()
        else:
            return self._get_patterns_in_memory()
    
    def _get_patterns_neo4j(self) -> List[Dict]:
        """Get patterns from Neo4j."""
        try:
            with self.driver.session() as session:
                result = session.run(
                    "MATCH (p:ProjectType)-[r]-(pl:Platform) "
                    "RETURN p.name as project_type, pl.name as platform, type(r) as relationship"
                )
                return [record.data() for record in result]
        except Exception:
            return []
    
    def _get_patterns_in_memory(self) -> List[Dict]:
        """Get patterns from in-memory storage."""
        return self.in_memory["relationships"]
    
    def get_patterns_for_project_type(self, project_type: str) -> List[Dict]:
        """Get all patterns for a specific project type."""
        all_patterns = self.get_all_patterns()
        return [p for p in all_patterns if p.get("project_type") == project_type]
    
    def get_success_rate(self, project_type: str, platform: str) -> float:
        """Calculate success rate for project type on platform."""
        patterns = self.get_all_patterns()
        
        relevant = [
            p for p in patterns 
            if p.get("project_type") == project_type and p.get("platform") == platform
        ]
        
        if not relevant:
            return 0.5  # Default when no data
        
        successes = sum(1 for p in relevant if p.get("outcome") == "success")
        return successes / len(relevant)
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# Global instance with environment-based configuration
pattern_graph = ProjectPatternGraph()


def update_project_pattern(project_type: str, platform: str, 
                          outcome: str, stage: int):
    """Convenience function to update pattern."""
    pattern_graph.update_project_pattern(project_type, platform, outcome, stage)


def get_all_patterns() -> List[Dict]:
    """Get all patterns."""
    return pattern_graph.get_all_patterns()


def get_patterns_for_project_type(project_type: str) -> List[Dict]:
    """Get patterns for project type."""
    return pattern_graph.get_patterns_for_project_type(project_type)


def get_success_rate(project_type: str, platform: str) -> float:
    """Get success rate."""
    return pattern_graph.get_success_rate(project_type, platform)
