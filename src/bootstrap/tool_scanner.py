import subprocess
import os
from typing import Dict, List

def scan_tools() -> Dict[str, str]:
    tools = {}
    required_tools = ["git", "npm", "netlify", "vercel", "surge", "gh", "python3", "node"]
    
    for tool in required_tools:
        try:
            result = subprocess.run([tool, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                tools[tool] = result.stdout.strip()
            else:
                tools[tool] = None
        except FileNotFoundError:
            tools[tool] = None
    
    return tools
