import hashlib
from typing import Dict, List

class DedupRegistry:
    def __init__(self):
        self.tool_registry = set()
        self.platform_registry = set()
        self.project_registry = set()
    
    def register_tool(self, tool_name: str, version: str):
        key = f"{tool_name}:{version}"
        self.tool_registry.add(key)
    
    def register_platform(self, platform_name: str, capabilities: Dict):
        # Create a hash of the capabilities
        capability_str = "|".join([f"{k}:{v}" for k, v in sorted(capabilities.items())])
        key = f"{platform_name}:{hashlib.sha256(capability_str.encode()).hexdigest()}"
        self.platform_registry.add(key)
    
    def register_project(self, project_path: str):
        # Calculate SHA256 of project files
        file_hash = hashlib.sha256()
        for root, dirs, files in os.walk(project_path):
            for file in sorted(files):
                with open(os.path.join(root, file), 'rb') as f:
                    file_hash.update(f.read())
        
        project_hash = file_hash.hexdigest()
        self.project_registry.add(project_hash)

# Global registry instance
registry = DedupRegistry()

def register_dedup(tools: Dict, platforms: List[Dict], project_type: str):
    # Register tools
    for tool_name, version in tools.items():
        if version:
            registry.register_tool(tool_name, version)
    
    # Register platforms
    for platform in platforms:
        registry.register_platform(platform["name"], platform)
    
    # Register project (this would be called from system scanner)
    # registry.register_project(project_path)
