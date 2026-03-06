import subprocess
import os
from typing import Dict, List


def scan_tools() -> Dict[str, str]:
    """
    Scan system for installed development and deployment tools.
    
    Checks:
    - Version control: git, gh (GitHub CLI)
    - Node.js ecosystem: node, npm, yarn, pnpm
    - Python ecosystem: python3, pip
    - Deployment CLIs: netlify, vercel, render, surge
    - Container: docker
    
    Returns:
        Dict mapping tool name to version string
    """
    tools = {}
    
    # Define tool commands to check
    tool_checks = {
        "git": ["git", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "yarn": ["yarn", "--version"],
        "python3": ["python3", "--version"],
        "pip": ["pip", "--version"],
        "docker": ["docker", "--version"],
        "gh": ["gh", "--version"],
    }
    
    # CLI tools that need special handling
    cli_tools = {
        "netlify": ["netlify", "--version"],
        "vercel": ["vercel", "--version"],
        "render": ["render", "--version"],
        "surge": ["surge", "--version"],
    }
    
    # Scan standard tools
    for tool_name, cmd in tool_checks.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                # Clean up version output
                version = version.replace("v", "").split("\n")[0]
                tools[tool_name] = version
            else:
                tools[tool_name] = None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            tools[tool_name] = None
    
    # Scan deployment CLIs (may not be installed)
    for tool_name, cmd in cli_tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                tools[tool_name] = version
            else:
                tools[tool_name] = None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            tools[tool_name] = None
    
    return tools


def get_tool_requirements(project_type: str) -> List[str]:
    """
    Get list of required tools for a project type.
    
    Args:
        project_type: Type of project (node, python, static, docker)
    
    Returns:
        List of required tool names
    """
    requirements = {
        "node": ["node", "npm", "git"],
        "python": ["python3", "pip", "git"],
        "static": ["git"],
        "docker": ["docker", "git"],
        "go": ["go", "git"],
        "rust": ["cargo", "git"],
    }
    
    return requirements.get(project_type, ["git"])


def check_tool_availability(tools: Dict[str, str], required: List[str]) -> Dict[str, bool]:
    """
    Check if required tools are available.
    
    Args:
        tools: Dict of installed tools
        required: List of required tool names
    
    Returns:
        Dict mapping tool name to availability status
    """
    return {
        tool: tool in tools and tools[tool] is not None
        for tool in required
    }
