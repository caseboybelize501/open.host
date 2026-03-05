import json
from pathlib import Path

def analyze_project(project_path: str):
    path = Path(project_path)
    
    # Extract metadata from project files
    metadata = {
        "project_type": None,
        "build_command": None,
        "output_dir": None,
        "environment_vars": [],
        "dependencies": [],
        "platform_hints": []
    }
    
    # Check for package.json (Node.js)
    if (path / "package.json").exists():
        with open(path / "package.json", 'r') as f:
            pkg = json.load(f)
        metadata["project_type"] = "node"
        metadata["build_command"] = pkg.get("scripts", {}).get("build", "npm run build")
        metadata["output_dir"] = "dist"
        
        # Extract dependencies
        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        metadata["dependencies"] = list(deps.keys()) + list(dev_deps.keys())
        
        # Platform hints
        if "react" in deps or "react-dom" in deps:
            metadata["platform_hints"].append("spa")
        
    # Check for requirements.txt (Python)
    elif (path / "requirements.txt").exists():
        metadata["project_type"] = "python"
        metadata["build_command"] = "pip install -r requirements.txt"
        metadata["output_dir"] = "dist"
        
        # Extract dependencies
        with open(path / "requirements.txt", 'r') as f:
            deps = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            metadata["dependencies"] = deps
        
    # Check for index.html (Static)
    elif (path / "index.html").exists():
        metadata["project_type"] = "static"
        metadata["build_command"] = "echo 'Static site'"
        metadata["output_dir"] = "."
        
    # Check for Dockerfile
    elif (path / "Dockerfile").exists():
        metadata["project_type"] = "docker"
        metadata["build_command"] = "docker build -t myapp ."
        metadata["output_dir"] = "."
        
    return metadata
