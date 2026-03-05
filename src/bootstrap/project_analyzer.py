import os
import json
import hashlib
from pathlib import Path

def analyze_project(project_path: str = "./") -> tuple:
    project_type = None
    build_settings = {}
    
    path = Path(project_path)
    
    # Check for package.json (Node.js)
    if (path / "package.json").exists():
        with open(path / "package.json", 'r') as f:
            pkg = json.load(f)
        project_type = "node"
        build_settings["build_command"] = pkg.get("scripts", {}).get("build", "npm run build")
        build_settings["output_dir"] = "dist"
        
    # Check for requirements.txt (Python)
    elif (path / "requirements.txt").exists():
        project_type = "python"
        build_settings["build_command"] = "pip install -r requirements.txt"
        build_settings["output_dir"] = "dist"
        
    # Check for index.html (Static)
    elif (path / "index.html").exists():
        project_type = "static"
        build_settings["build_command"] = "echo 'Static site'"
        build_settings["output_dir"] = "."
        
    # Check for Dockerfile
    elif (path / "Dockerfile").exists():
        project_type = "docker"
        build_settings["build_command"] = "docker build -t myapp ."
        build_settings["output_dir"] = "."
        
    # Default to static if nothing found
    else:
        project_type = "static"
        build_settings["build_command"] = "echo 'Static site'"
        build_settings["output_dir"] = "."
        
    return project_type, build_settings
