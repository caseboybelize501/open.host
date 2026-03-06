import json
from pathlib import Path
from typing import Dict, List, Optional


class ProjectAnalyzer:
    """
    Analyzes project structure to determine type, build requirements, and platform hints.
    
    Supports:
    - Node.js (package.json)
    - Python (requirements.txt, setup.py)
    - Static sites (index.html)
    - Docker projects (Dockerfile)
    - Next.js, React, Vue, Angular frameworks
    """
    
    def __init__(self):
        self.framework_signatures = {
            'react': ['react', 'react-dom'],
            'next': ['next', 'next.js'],
            'vue': ['vue', 'vue-router'],
            'angular': ['@angular/core', '@angular/cli'],
            'svelte': ['svelte'],
            'gatsby': ['gatsby'],
            'nuxt': ['nuxt', 'nuxt.js'],
            'remix': ['@remix-run/react'],
        }
    
    def analyze_project(self, project_path: str) -> Dict:
        """
        Analyze project at given path and return metadata.
        
        Returns:
            Dict with project_type, build_command, output_dir, 
            environment_vars, dependencies, platform_hints
        """
        path = Path(project_path)
        
        if not path.exists():
            return self._create_error_result(f"Path does not exist: {project_path}")
        
        metadata = {
            "project_type": None,
            "framework": None,
            "build_command": None,
            "output_dir": None,
            "environment_vars": [],
            "dependencies": [],
            "platform_hints": [],
            "source_dir": str(path)
        }
        
        # Check for package.json (Node.js)
        if (path / "package.json").exists():
            metadata.update(self._analyze_node_project(path))
        
        # Check for requirements.txt or setup.py (Python)
        elif (path / "requirements.txt").exists() or (path / "setup.py").exists():
            metadata.update(self._analyze_python_project(path))
        
        # Check for index.html (Static)
        elif (path / "index.html").exists():
            metadata.update(self._analyze_static_project(path))
        
        # Check for Dockerfile
        elif (path / "Dockerfile").exists():
            metadata.update(self._analyze_docker_project(path))
        
        # Check for Go project
        elif (path / "go.mod").exists():
            metadata.update(self._analyze_go_project(path))
        
        # Check for Rust project
        elif (path / "Cargo.toml").exists():
            metadata.update(self._analyze_rust_project(path))
        
        else:
            return self._create_error_result("Unknown project type - no recognized config files found")
        
        return metadata
    
    def _analyze_node_project(self, path: Path) -> Dict:
        """Analyze Node.js project."""
        metadata = {
            "project_type": "node",
            "build_command": "npm run build",
            "output_dir": "dist",
            "environment_vars": [],
            "dependencies": [],
            "platform_hints": []
        }
        
        try:
            with open(path / "package.json", 'r') as f:
                pkg = json.load(f)
            
            # Extract scripts
            scripts = pkg.get("scripts", {})
            metadata["build_command"] = scripts.get("build", "npm run build")
            
            # Extract dependencies
            deps = list(pkg.get("dependencies", {}).keys())
            dev_deps = list(pkg.get("devDependencies", {}).keys())
            metadata["dependencies"] = deps + dev_deps
            
            # Detect framework
            metadata["framework"] = self._detect_framework(deps + dev_deps)
            
            # Set output dir based on framework
            if metadata["framework"] == "next":
                metadata["output_dir"] = ".next"
                metadata["platform_hints"].append("serverless")
                metadata["platform_hints"].append("ssr")
            elif metadata["framework"] == "gatsby":
                metadata["output_dir"] = "public"
            elif metadata["framework"] in ["react", "vue", "angular", "svelte"]:
                metadata["output_dir"] = "dist"
                metadata["platform_hints"].append("spa")
            elif metadata["framework"] == "nuxt":
                metadata["output_dir"] = ".output"
                metadata["platform_hints"].append("ssr")
            
            # Check for API routes (Next.js, Remix)
            if (path / "api").exists() or (path / "pages" / "api").exists():
                metadata["platform_hints"].append("api_routes")
            
            # Check for environment requirements
            if (path / ".env.example").exists() or (path / ".env.local").exists():
                metadata["environment_vars"] = self._extract_env_vars(path)
            
        except Exception as e:
            metadata["error"] = f"Failed to parse package.json: {str(e)}"
        
        return metadata
    
    def _analyze_python_project(self, path: Path) -> Dict:
        """Analyze Python project."""
        metadata = {
            "project_type": "python",
            "framework": None,
            "build_command": "pip install -r requirements.txt",
            "output_dir": ".",
            "environment_vars": [],
            "dependencies": [],
            "platform_hints": []
        }
        
        try:
            # Read requirements.txt
            if (path / "requirements.txt").exists():
                with open(path / "requirements.txt", 'r') as f:
                    deps = [line.strip().split('==')[0].split('>=')[0] 
                           for line in f if line.strip() and not line.startswith('#')]
                    metadata["dependencies"] = deps
                    
                    # Detect framework
                    if any('flask' in d.lower() for d in deps):
                        metadata["framework"] = "flask"
                        metadata["platform_hints"].append("wsgi")
                    elif any('django' in d.lower() for d in deps):
                        metadata["framework"] = "django"
                        metadata["platform_hints"].append("wsgi")
                    elif any('fastapi' in d.lower() for d in deps):
                        metadata["framework"] = "fastapi"
                        metadata["platform_hints"].append("asgi")
            
            # Check for app.py or main.py
            if (path / "app.py").exists() or (path / "main.py").exists():
                metadata["platform_hints"].append("has_entrypoint")
            
        except Exception as e:
            metadata["error"] = f"Failed to analyze Python project: {str(e)}"
        
        return metadata
    
    def _analyze_static_project(self, path: Path) -> Dict:
        """Analyze static site project."""
        return {
            "project_type": "static",
            "framework": "static",
            "build_command": "echo 'Static site - no build required'",
            "output_dir": ".",
            "environment_vars": [],
            "dependencies": [],
            "platform_hints": ["static", "cdn"]
        }
    
    def _analyze_docker_project(self, path: Path) -> Dict:
        """Analyze Docker project."""
        metadata = {
            "project_type": "docker",
            "framework": None,
            "build_command": "docker build -t myapp .",
            "output_dir": ".",
            "environment_vars": [],
            "dependencies": [],
            "platform_hints": ["docker", "container"]
        }
        
        try:
            with open(path / "Dockerfile", 'r') as f:
                content = f.read().lower()
                
                # Detect base image type
                if 'node' in content:
                    metadata["framework"] = "node-docker"
                elif 'python' in content:
                    metadata["framework"] = "python-docker"
                elif 'nginx' in content:
                    metadata["framework"] = "nginx"
                    metadata["platform_hints"].append("static")
                    
        except Exception as e:
            metadata["error"] = f"Failed to analyze Dockerfile: {str(e)}"
        
        return metadata
    
    def _analyze_go_project(self, path: Path) -> Dict:
        """Analyze Go project."""
        return {
            "project_type": "go",
            "framework": "go",
            "build_command": "go build -o app",
            "output_dir": ".",
            "environment_vars": [],
            "dependencies": [],
            "platform_hints": ["binary", "server"]
        }
    
    def _analyze_rust_project(self, path: Path) -> Dict:
        """Analyze Rust project."""
        return {
            "project_type": "rust",
            "framework": "rust",
            "build_command": "cargo build --release",
            "output_dir": "target/release",
            "environment_vars": [],
            "dependencies": [],
            "platform_hints": ["binary", "wasm"]
        }
    
    def _detect_framework(self, dependencies: List[str]) -> Optional[str]:
        """Detect framework from dependencies."""
        for framework, signatures in self.framework_signatures.items():
            if any(sig in dep.lower() for dep in dependencies for sig in signatures):
                return framework
        return None
    
    def _extract_env_vars(self, path: Path) -> List[str]:
        """Extract environment variable names from .env files."""
        env_vars = []
        env_files = ['.env.example', '.env.local', '.env.template']
        
        for env_file in env_files:
            file_path = path / env_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                var_name = line.split('=')[0]
                                env_vars.append(var_name)
                except:
                    pass
        
        return env_vars
    
    def _create_error_result(self, error: str) -> Dict:
        """Create error result."""
        return {
            "project_type": None,
            "build_command": None,
            "output_dir": None,
            "environment_vars": [],
            "dependencies": [],
            "platform_hints": [],
            "error": error
        }


# Global instance
project_analyzer = ProjectAnalyzer()


def analyze_project(project_path: str) -> Dict:
    """Convenience function to analyze project."""
    return project_analyzer.analyze_project(project_path)
