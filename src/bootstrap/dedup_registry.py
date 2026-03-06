import hashlib
import os
from typing import Dict, List, Any
from pathlib import Path


class DedupRegistry:
    """
    Deduplication registry to avoid redundant scans and reprocessing.
    
    Follows the HARD REQUIREMENT 2 from the original prompt:
    - EDA tool registry (path + version)
    - IP core catalog (name + version hash)
    - Model files (sha256)
    
    Adapted for hosting deployment:
    - Tool registry (name + version)
    - Platform registry (name + capabilities hash)
    - Project registry (path + content hash)
    """
    
    def __init__(self):
        self.tool_registry: set = set()
        self.platform_registry: set = set()
        self.project_registry: set = set()
        self.scan_history: List[Dict] = []
    
    def register_tool(self, tool_name: str, version: str):
        """Register a tool version to avoid re-scanning."""
        key = f"{tool_name}:{version}"
        self.tool_registry.add(key)
    
    def register_platform(self, platform_name: str, capabilities: Dict):
        """Register platform configuration."""
        # Create a hash of the capabilities
        capability_str = "|".join([f"{k}:{v}" for k, v in sorted(capabilities.items())])
        key = f"{platform_name}:{hashlib.sha256(capability_str.encode()).hexdigest()}"
        self.platform_registry.add(key)
    
    def register_project(self, project_path: str):
        """Register project by hashing its files."""
        project_hash = self._hash_project_files(project_path)
        if project_hash:
            self.project_registry.add(project_hash)
    
    def _hash_project_files(self, project_path: str) -> str:
        """Calculate SHA256 of project files."""
        file_hash = hashlib.sha256()
        path = Path(project_path)
        
        if not path.exists():
            return ""
        
        # Files to include in hash
        files_to_hash = [
            "package.json",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            "Cargo.toml",
            "go.mod",
            "index.html",
        ]
        
        for filename in files_to_hash:
            file_path = path / filename
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    file_hash.update(f.read())
        
        return file_hash.hexdigest()
    
    def is_tool_known(self, tool_name: str, version: str) -> bool:
        """Check if tool version is already registered."""
        key = f"{tool_name}:{version}"
        return key in self.tool_registry
    
    def is_platform_known(self, platform_name: str, capabilities: Dict) -> bool:
        """Check if platform configuration is already registered."""
        capability_str = "|".join([f"{k}:{v}" for k, v in sorted(capabilities.items())])
        key = f"{platform_name}:{hashlib.sha256(capability_str.encode()).hexdigest()}"
        return key in self.platform_registry
    
    def is_project_known(self, project_path: str) -> bool:
        """Check if project is already registered."""
        project_hash = self._hash_project_files(project_path)
        return project_hash in self.project_registry
    
    def get_registry_summary(self) -> Dict:
        """Get summary of registry contents."""
        return {
            "tools": len(self.tool_registry),
            "platforms": len(self.platform_registry),
            "projects": len(self.project_registry),
            "scan_history": len(self.scan_history)
        }
    
    def record_scan(self, scan_type: str, result: Any):
        """Record a scan in history."""
        self.scan_history.append({
            "type": scan_type,
            "timestamp": self._get_timestamp(),
            "result_summary": str(result)[:100] if result else None
        })
        
        # Keep only last 100 scans
        if len(self.scan_history) > 100:
            self.scan_history = self.scan_history[-100:]
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()


# Global registry instance
registry = DedupRegistry()


def register_dedup(tools: Dict, platforms: List[Dict], project_info: Dict):
    """
    Register all detected items in dedup registry.
    
    Args:
        tools: Dict of tool names to versions
        platforms: List of platform configurations
        project_info: Project information dict
    """
    # Register tools
    for tool_name, version in tools.items():
        if version:
            registry.register_tool(tool_name, version)
            registry.record_scan("tool", {tool_name: version})
    
    # Register platforms
    for platform in platforms:
        registry.register_platform(platform["name"], platform)
        registry.record_scan("platform", platform["name"])
    
    # Register project if path provided
    if project_info and "source_dir" in project_info:
        registry.register_project(project_info["source_dir"])
        registry.record_scan("project", project_info["source_dir"])


def get_registry() -> DedupRegistry:
    """Get global registry instance."""
    return registry


def get_registry_summary() -> Dict:
    """Get registry summary."""
    return registry.get_registry_summary()
