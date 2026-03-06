"""
Local GGUF Model Pool Manager

Scans C:/ and D:/ drives for GGUF model files and manages a pool
of locally available models for offline inference.

Supports:
- llama-cpp-python backend
- Multiple model sizes (1B for agents, 7B+ for master)
- Model hot-swapping based on task
- VRAM-aware loading
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class GGUFModel:
    """Represents a GGUF model file."""
    path: str
    name: str
    size_gb: float
    sha256: str
    model_type: str  # master, analyzer, deploy, memory
    parameters: str  # e.g., "7B", "13B", "1B"
    quantization: str  # e.g., "Q4_K_M", "Q5_K_M", "F16"
    loaded: bool = False


class GGUFModelPool:
    """
    Manages pool of local GGUF models.
    
    Scans configured directories for .gguf files and maintains
    a registry of available models with metadata.
    """
    
    def __init__(self):
        self.models: Dict[str, GGUFModel] = {}
        self.loaded_models: Dict[str, Any] = {}  # model_name -> llama.Llama instance
        self.scan_paths = self._get_default_scan_paths()
        self.max_loaded_models = 2  # Limit concurrent loaded models
        self._llama = None
    
    def _get_default_scan_paths(self) -> List[Path]:
        """Get default paths to scan for GGUF models."""
        paths = []
        
        # Windows default paths
        windows_paths = [
            Path("C:/models"),
            Path("C:/models/gguf"),
            Path("C:/Users") / os.getenv("USERNAME", "") / "models",
            Path("D:/models"),
            Path("D:/models/gguf"),
            Path("D:/AI"),
            Path("D:/AI/models"),
        ]
        
        # Linux/Mac paths
        unix_paths = [
            Path.home() / "models",
            Path("/models"),
            Path("/opt/models"),
        ]
        
        if os.name == 'nt':
            paths.extend(windows_paths)
        else:
            paths.extend(unix_paths)
        
        return [p for p in paths if p.exists()]
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of model file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error hashing {file_path}: {e}")
            return ""
    
    def _parse_model_name(self, filename: str) -> Dict[str, str]:
        """
        Parse model metadata from filename.
        
        Examples:
        - llama-2-7b.Q4_K_M.gguf -> {type: llama, params: 7B, quant: Q4_K_M}
        - phi-3-mini-4k-instruct.Q5_K_M.gguf -> {type: phi, params: ~3B, quant: Q5_K_M}
        - mistral-7b-instruct-v0.2.Q4_K_M.gguf
        """
        name_lower = filename.lower()
        
        # Extract parameter size
        params = "unknown"
        if "70b" in name_lower or "70b" in filename.lower():
            params = "70B"
        elif "34b" in name_lower:
            params = "34B"
        elif "13b" in name_lower:
            params = "13B"
        elif "7b" in name_lower:
            params = "7B"
        elif "3b" in name_lower:
            params = "3B"
        elif "1b" in name_lower or "mini" in name_lower:
            params = "1-3B"
        elif "tiny" in name_lower:
            params = "<1B"
        
        # Extract quantization
        quant = "unknown"
        for q in ["Q2_K", "Q3_K_S", "Q3_K_M", "Q3_K_L", "Q4_K_S", "Q4_K_M", 
                  "Q5_K_S", "Q5_K_M", "Q6_K", "Q8_0", "F16", "F32"]:
            if q.lower() in name_lower:
                quant = q
                break
        
        # Determine model type based on size
        model_type = "analyzer"  # Default small model for agents
        if "70b" in name_lower or "34b" in name_lower or "13b" in name_lower:
            model_type = "master"
        elif "7b" in name_lower:
            model_type = "master"  # 7B can be master or analyzer
        
        # Check for specific model purposes
        if "deploy" in name_lower or "code" in name_lower:
            model_type = "deploy"
        elif "memory" in name_lower or "embed" in name_lower:
            model_type = "memory"
        
        return {
            "parameters": params,
            "quantization": quant,
            "model_type": model_type
        }
    
    def scan_for_models(self) -> List[GGUFModel]:
        """Scan all configured paths for GGUF model files."""
        found_models = []
        
        for scan_path in self.scan_paths:
            if not scan_path.exists():
                continue
            
            print(f"Scanning {scan_path} for GGUF models...")
            
            try:
                for gguf_file in scan_path.rglob("*.gguf"):
                    if gguf_file.is_file():
                        model = self._create_model_entry(gguf_file)
                        if model:
                            found_models.append(model)
                            self.models[model.path] = model
            except Exception as e:
                print(f"Error scanning {scan_path}: {e}")
        
        print(f"Found {len(found_models)} GGUF models")
        return found_models
    
    def _create_model_entry(self, file_path: Path) -> Optional[GGUFModel]:
        """Create GGUFModel entry from file."""
        try:
            file_size_gb = file_path.stat().st_size / (1024 ** 3)
            metadata = self._parse_model_name(file_path.name)
            
            return GGUFModel(
                path=str(file_path),
                name=file_path.stem,
                size_gb=round(file_size_gb, 2),
                sha256=self._calculate_sha256(file_path),
                model_type=metadata["model_type"],
                parameters=metadata["parameters"],
                quantization=metadata["quantization"],
                loaded=False
            )
        except Exception as e:
            print(f"Error creating model entry for {file_path}: {e}")
            return None
    
    def get_model(self, model_type: str = "analyzer") -> Optional[GGUFModel]:
        """
        Get a model of specified type from pool.
        
        Args:
            model_type: One of 'master', 'analyzer', 'deploy', 'memory'
        
        Returns:
            GGUFModel or None if not available
        """
        # Find unloaded model of specified type
        for model in self.models.values():
            if model.model_type == model_type and not model.loaded:
                return model
        
        # If all loaded, return any model of correct type
        for model in self.models.values():
            if model.model_type == model_type:
                return model
        
        return None
    
    def load_model(self, model_path: str, n_ctx: int = 2048, 
                   n_gpu_layers: int = 0) -> Optional[Any]:
        """
        Load a GGUF model using llama-cpp-python.
        
        Args:
            model_path: Path to .gguf file
            n_ctx: Context window size
            n_gpu_layers: Number of layers to offload to GPU (0 = CPU only)
        
        Returns:
            llama.Llama instance or None
        """
        try:
            from llama_cpp import Llama
            
            # Check if already loaded
            if model_path in self.loaded_models:
                return self.loaded_models[model_path]
            
            # Unload oldest model if at capacity
            if len(self.loaded_models) >= self.max_loaded_models:
                self._unload_oldest_model()
            
            print(f"Loading model: {model_path}")
            print(f"  Context: {n_ctx}, GPU layers: {n_gpu_layers}")
            
            # Load model
            llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            self.loaded_models[model_path] = llm
            
            # Update model status
            if model_path in self.models:
                self.models[model_path].loaded = True
            
            print(f"Model loaded successfully: {model_path}")
            return llm
            
        except ImportError:
            print("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            return None
        except Exception as e:
            print(f"Error loading model {model_path}: {e}")
            return None
    
    def _unload_oldest_model(self):
        """Unload oldest loaded model to free memory."""
        if self.loaded_models:
            oldest_path = next(iter(self.loaded_models))
            self.unload_model(oldest_path)
    
    def unload_model(self, model_path: str):
        """Unload a model from memory."""
        if model_path in self.loaded_models:
            del self.loaded_models[model_path]
            print(f"Unloaded model: {model_path}")
            
            if model_path in self.models:
                self.models[model_path].loaded = False
    
    def generate(self, model_path: str, prompt: str, 
                 max_tokens: int = 512, temperature: float = 0.7,
                 stop: Optional[List[str]] = None) -> str:
        """
        Generate text using a loaded model.
        
        Args:
            model_path: Path to model
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences
        
        Returns:
            Generated text
        """
        # Load model if needed
        if model_path not in self.loaded_models:
            llm = self.load_model(model_path)
            if not llm:
                return ""
        else:
            llm = self.loaded_models[model_path]
        
        # Generate
        output = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or [],
            echo=False
        )
        
        return output["choices"][0]["text"].strip()
    
    def get_available_models_summary(self) -> Dict:
        """Get summary of available models."""
        summary = {
            "total_models": len(self.models),
            "loaded_models": len(self.loaded_models),
            "by_type": {
                "master": [],
                "analyzer": [],
                "deploy": [],
                "memory": []
            },
            "scan_paths": [str(p) for p in self.scan_paths]
        }
        
        for model in self.models.values():
            summary["by_type"][model.model_type].append({
                "name": model.name,
                "size_gb": model.size_gb,
                "parameters": model.parameters,
                "quantization": model.quantization,
                "loaded": model.loaded
            })
        
        return summary
    
    def recommend_model_for_task(self, task: str) -> Optional[GGUFModel]:
        """
        Recommend best model for a given task.
        
        Tasks:
        - complex_reasoning, planning, orchestration -> master model
        - code_analysis, tech_stack, risk_assessment -> analyzer model
        - deployment, config_generation -> deploy model
        - memory_query, embedding -> memory model
        """
        task_to_type = {
            "complex_reasoning": "master",
            "planning": "master",
            "orchestration": "master",
            "decision": "master",
            "code_analysis": "analyzer",
            "tech_stack": "analyzer",
            "risk_assessment": "analyzer",
            "deployment": "deploy",
            "config": "deploy",
            "memory": "memory",
            "embedding": "memory",
        }
        
        # Determine model type from task
        model_type = "analyzer"  # default
        for keyword, mtype in task_to_type.items():
            if keyword in task.lower():
                model_type = mtype
                break
        
        return self.get_model(model_type)


# Global singleton instance
_model_pool: Optional[GGUFModelPool] = None


def get_model_pool() -> GGUFModelPool:
    """Get global model pool instance."""
    global _model_pool
    if _model_pool is None:
        _model_pool = GGUFModelPool()
    return _model_pool


def scan_models() -> List[GGUFModel]:
    """Scan for models."""
    return get_model_pool().scan_for_models()


def get_model_summary() -> Dict:
    """Get model summary."""
    return get_model_pool().get_available_models_summary()
