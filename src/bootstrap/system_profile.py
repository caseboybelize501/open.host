from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


class HostingSystemProfile(BaseModel):
    """
    System profile containing all detected tools, platforms, and credentials.
    
    Written during startup bootstrap before any agents activate.
    Follows the pattern from the original FPGA prompt's FPGASystemProfile.
    """
    
    # Tool detection results
    tools: Dict[str, str] = Field(default_factory=dict, description="Detected tools and versions")
    
    # Project analysis
    project_type: Optional[str] = Field(default=None, description="Default project type")
    build_settings: Dict[str, Any] = Field(default_factory=dict, description="Build configuration")
    
    # Platform information
    platforms: List[Dict[str, Any]] = Field(default_factory=list, description="Available hosting platforms")
    
    # Credentials
    credentials: Dict[str, str] = Field(default_factory=dict, description="Platform credentials")
    
    # Inference configuration (for future LLM integration)
    inference_config: Dict[str, Any] = Field(default_factory=dict, description="LLM inference configuration")
    
    # Hardware inventory (for future expansion)
    hardware_inventory: Dict[str, Any] = Field(default_factory=dict, description="Connected hardware")
    
    # System capabilities
    capabilities: Dict[str, bool] = Field(default_factory=dict, description="System capabilities")
    
    # Validation state
    validation_state: Dict[str, Any] = Field(default_factory=dict, description="Validation cycle state")
    
    # Memory state references
    memory_state: Dict[str, Any] = Field(default_factory=dict, description="Memory system state")
    
    class Config:
        extra = "allow"
        arbitrary_types_allowed = True
    
    @classmethod
    def load_from_file(cls, path: str = "system_profile.json") -> "HostingSystemProfile":
        """Load profile from JSON file."""
        profile_path = Path(path)
        if not profile_path.exists():
            return cls()
        
        try:
            with open(profile_path, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            print(f"Failed to load profile: {e}")
            return cls()
    
    def save_to_file(self, path: str = "system_profile.json"):
        """Save profile to JSON file."""
        profile_path = Path(path)
        try:
            with open(profile_path, 'w') as f:
                json.dump(self.model_dump(), f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save profile: {e}")
    
    def is_validated(self) -> bool:
        """Check if profile has been validated (minimum requirements met)."""
        # Must have at least some tools detected
        if not self.tools:
            return False
        
        # Must have at least one platform available
        if not self.platforms:
            return False
        
        return True
    
    def get_tool_version(self, tool_name: str) -> Optional[str]:
        """Get version of a specific tool."""
        return self.tools.get(tool_name)
    
    def has_credential(self, platform: str) -> bool:
        """Check if credential exists for platform."""
        return platform in self.credentials
    
    def get_platform(self, platform_name: str) -> Optional[Dict]:
        """Get platform information by name."""
        for platform in self.platforms:
            if platform.get("name") == platform_name:
                return platform
        return None
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get system capabilities."""
        capabilities = {
            "node_deploy": self.tools.get("node") is not None and self.tools.get("npm") is not None,
            "python_deploy": self.tools.get("python3") is not None,
            "docker_deploy": self.tools.get("docker") is not None,
            "netlify": self.has_credential("netlify") or self.tools.get("netlify") is not None,
            "vercel": self.has_credential("vercel") or self.tools.get("vercel") is not None,
            "github_pages": self.has_credential("github") or self.tools.get("gh") is not None,
            "render": self.has_credential("render") or self.tools.get("render") is not None,
        }
        return capabilities
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=== Hosting System Profile ===",
            f"Tools: {len(self.tools)} detected",
            f"Platforms: {len(self.platforms)} available",
            f"Credentials: {len(self.credentials)} configured",
            f"Validated: {self.is_validated()}",
        ]
        return "\n".join(lines)


# Global singleton instance
_profile_instance: Optional[HostingSystemProfile] = None


def get_profile() -> HostingSystemProfile:
    """Get the global system profile instance."""
    global _profile_instance
    if _profile_instance is None:
        _profile_instance = HostingSystemProfile()
    return _profile_instance


def set_profile(profile: HostingSystemProfile):
    """Set the global system profile instance."""
    global _profile_instance
    _profile_instance = profile


def update_profile(**kwargs):
    """Update profile with new values."""
    profile = get_profile()
    for key, value in kwargs.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    return profile
