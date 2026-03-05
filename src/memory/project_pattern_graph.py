from neo4j import GraphDatabase

class ProjectPatternGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def update_project_pattern(self, project_type: str, platform: str, outcome: str,
                              stage: int):
        with self.driver.session() as session:
            session.write_transaction(
                self._create_project_pattern,
                project_type, platform, outcome, stage
            )
    
    @staticmethod
    def _create_project_pattern(tx, project_type: str, platform: str, outcome: str,
                               stage: int):
        query = (
            "MERGE (p:ProjectType {name: $project_type}) "
            "MERGE (pl:Platform {name: $platform}) "
            "MERGE (p)-[:SUCCEEDS_ON]->(pl) "
            "SET pl.last_used = timestamp()"
        )
        tx.run(query, project_type=project_type, platform=platform)

# Global instance
pattern_graph = ProjectPatternGraph("bolt://localhost:7687", "neo4j", "password")

def update_project_pattern(project_type: str, platform: str, outcome: str, stage: int):
    pattern_graph.update_project_pattern(project_type, platform, outcome, stage)
