#!/usr/bin/env python3
"""
Deep System Scan - Hardware, Software, and GGUF Model Discovery
Scans C:/ and D:/ drives comprehensively
"""

import os
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

RESULTS = {
    "scan_date": datetime.now().isoformat(),
    "hardware": {},
    "software": {},
    "gguf_models": [],
    "drive_space": {},
    "python_packages": [],
    "node_packages": [],
    "architecture": {}
}

def run_command(cmd):
    """Run shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def scan_hardware():
    """Scan hardware configuration."""
    print("  Scanning hardware...")
    
    # CPU Info
    cpu_cmd = 'wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed /format:list'
    cpu_info = run_command(cpu_cmd)
    
    # RAM Info
    ram_cmd = 'wmic memorychip get Capacity,Speed,Manufacturer /format:list'
    ram_info = run_command(ram_cmd)
    
    # GPU Info
    gpu_cmd = 'wmic path win32_videocontroller get Name,DriverVersion,AdapterRAM /format:list'
    gpu_info = run_command(gpu_cmd)
    
    # Baseboard/Motherboard
    board_cmd = 'wmic baseboard get Manufacturer,Product /format:list'
    board_info = run_command(board_cmd)
    
    # OS Info
    os_cmd = 'wmic os get Caption,Version,OSArchitecture,TotalVisibleMemorySize /format:list'
    os_info = run_command(os_cmd)
    
    RESULTS["hardware"] = {
        "cpu": cpu_info,
        "ram": ram_info,
        "gpu": gpu_info,
        "motherboard": board_info,
        "os": os_info
    }
    
    # Get GPU details via DirectX Diagnostic
    dxdiag = run_command('dxdiag /t')
    if dxdiag:
        RESULTS["hardware"]["dxdiag"] = dxdiag[:5000]  # First 5000 chars

def scan_software():
    """Scan installed software."""
    print("  Scanning software...")
    
    # Python
    python_version = run_command('python --version')
    python_path = run_command('where python')
    pip_list = run_command('pip list --format=json')
    
    # Node.js
    node_version = run_command('node --version')
    npm_version = run_command('npm --version')
    node_path = run_command('where node')
    
    # Git
    git_version = run_command('git --version')
    
    # Docker
    docker_version = run_command('docker --version')
    docker_compose = run_command('docker compose version')
    
    # CUDA
    cuda_version = run_command('nvcc --version')
    
    # Visual Studio
    vs_where = run_command('"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.Component.MSBuild -format json')
    
    RESULTS["software"] = {
        "python": {
            "version": python_version,
            "path": python_path,
        },
        "nodejs": {
            "version": node_version,
            "npm_version": npm_version,
            "path": node_path
        },
        "git": git_version,
        "docker": {
            "version": docker_version,
            "compose": docker_compose
        },
        "cuda": cuda_version,
        "packages_raw": pip_list
    }
    
    # Parse pip list
    try:
        RESULTS["python_packages"] = json.loads(pip_list) if pip_list and not pip_list.startswith("Error") else []
    except:
        RESULTS["python_packages"] = []

def scan_architecture():
    """Scan system architecture."""
    print("  Scanning architecture...")
    
    # System info
    sysinfo = run_command('systeminfo')
    
    # Processor architecture
    arch = run_command('echo %PROCESSOR_ARCHITECTURE%')
    
    # Virtualization
    virt = run_command('systeminfo | findstr /C:"Hyper-V"')
    
    RESULTS["architecture"] = {
        "processor_arch": arch,
        "systeminfo": sysinfo[:10000] if sysinfo else "",
        "virtualization": virt
    }

def scan_drive_space():
    """Scan drive space."""
    print("  Scanning drive space...")
    
    for drive in ['C:', 'D:', 'E:', 'F:']:
        if os.path.exists(drive):
            try:
                total, used, free = os.statvfs(drive) if os.name != 'nt' else (0, 0, 0)
                # Windows alternative
                wmic = run_command(f'wmic logicaldisk where "DeviceID=\'{drive}\'" get Size,FreeSpace /format:list')
                RESULTS["drive_space"][drive] = wmic
            except:
                RESULTS["drive_space"][drive] = "Accessible"

def scan_gguf_models():
    """Deep scan for GGUF model files."""
    print("  Scanning for GGUF models (deep scan)...")
    
    gguf_paths = []
    search_dirs = [
        'C:/',
        'D:/',
        'C:/models',
        'C:/models/gguf',
        'D:/models',
        'D:/models/gguf',
        'D:/AI',
        'D:/AI/models',
        'D:/AI/models/gguf',
        os.path.expanduser('~'),
        os.path.expanduser('~') + '/.cache/lm-studio/models',
        os.path.expanduser('~') + '/.cache/huggingface'
    ]
    
    # Also check common directories
    for base in ['C:', 'D:']:
        for subdir in ['Users', 'Projects', 'AI', 'ML', 'Models', 'Downloads']:
            search_dirs.append(f'{base}/{subdir}')
    
    gguf_pattern = re.compile(r'.*\.gguf$', re.IGNORECASE)
    
    scanned = 0
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            try:
                for root, dirs, files in os.walk(search_dir, followlinks=False):
                    # Skip hidden and system directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for file in files:
                        if gguf_pattern.match(file):
                            full_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(full_path)
                                size_gb = size / (1024**3)
                                gguf_paths.append({
                                    "path": full_path,
                                    "filename": file,
                                    "size_bytes": size,
                                    "size_gb": round(size_gb, 2),
                                    "directory": root
                                })
                                print(f"    Found: {file} ({size_gb:.2f} GB)")
                            except Exception as e:
                                gguf_paths.append({
                                    "path": full_path,
                                    "filename": file,
                                    "error": str(e)
                                })
                    scanned += 1
                    if scanned % 1000 == 0:
                        print(f"    Scanned {scanned} directories...")
            except PermissionError:
                pass
            except Exception as e:
                print(f"    Error scanning {search_dir}: {e}")
    
    RESULTS["gguf_models"] = gguf_paths
    print(f"  Total GGUF models found: {len(gguf_paths)}")

def scan_llm_software():
    """Scan for LLM-related software."""
    print("  Scanning LLM software...")
    
    # Check for llama.cpp
    llama_cpp = run_command('where llama-cli')
    
    # Check for Ollama
    ollama = run_command('ollama --version')
    
    # Check for LM Studio
    lm_studio_paths = [
        os.path.expanduser('~') + '/.cache/lm-studio',
        'C:/Program Files/LM Studio',
        'D:/Program Files/LM Studio'
    ]
    
    lm_studio_exists = any(os.path.exists(p) for p in lm_studio_paths)
    
    # Check for Oobabooga
    ooba_paths = [
        'C:/oobabooga',
        'D:/oobabooga',
        os.path.expanduser('~') + '/text-generation-webui'
    ]
    
    ooba_exists = any(os.path.exists(p) for p in ooba_paths)
    
    RESULTS["software"]["llm"] = {
        "llama_cpp": llama_cpp if llama_cpp and not llama_cpp.startswith("Error") else "Not found",
        "ollama": ollama if ollama and not ollama.startswith("Error") else "Not found",
        "lm_studio": "Installed" if lm_studio_exists else "Not found",
        "oobabooga": "Installed" if ooba_exists else "Not found"
    }

def scan_docker_images():
    """Scan Docker images."""
    print("  Scanning Docker images...")
    
    docker_images = run_command('docker images --format "{{.Repository}}:{{.Tag}} - {{.Size}}"')
    docker_containers = run_command('docker ps -a --format "{{.Names}} - {{.Status}}"')
    
    RESULTS["software"]["docker"]["images"] = docker_images if docker_images and not docker_images.startswith("Error") else "None or Docker not running"
    RESULTS["software"]["docker"]["containers"] = docker_containers if docker_containers and not docker_containers.startswith("Error") else "None or Docker not running"

def main():
    print("=" * 80)
    print("DEEP SYSTEM SCAN - Hardware, Software, GGUF Models")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    scan_hardware()
    scan_software()
    scan_architecture()
    scan_drive_space()
    scan_gguf_models()
    scan_llm_software()
    scan_docker_images()
    
    # Save results
    output_file = 'SYSTEM.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# SYSTEM HARDWARE & SOFTWARE INVENTORY\n\n")
        f.write(f"**Scan Date**: {RESULTS['scan_date']}\n\n")
        f.write(f"**Generated by**: deep_system_scan.py\n\n")
        f.write("---\n\n")
        
        # Hardware Section
        f.write("## HARDWARE\n\n")
        f.write("### CPU\n```\n")
        f.write(RESULTS["hardware"].get("cpu", "Not available") + "\n```\n\n")
        
        f.write("### GPU\n```\n")
        f.write(RESULTS["hardware"].get("gpu", "Not available") + "\n```\n\n")
        
        f.write("### RAM\n```\n")
        f.write(RESULTS["hardware"].get("ram", "Not available") + "\n```\n\n")
        
        f.write("### Motherboard\n```\n")
        f.write(RESULTS["hardware"].get("motherboard", "Not available") + "\n```\n\n")
        
        f.write("### Operating System\n```\n")
        f.write(RESULTS["hardware"].get("os", "Not available") + "\n```\n\n")
        
        # Architecture Section
        f.write("## ARCHITECTURE\n\n")
        f.write(f"**Processor Architecture**: {RESULTS['architecture'].get('processor_arch', 'Unknown')}\n\n")
        f.write("<details>\n<summary>Full System Info (click to expand)</summary>\n\n```")
        f.write(RESULTS["architecture"].get("systeminfo", "Not available") + "\n```\n\n</details>\n\n")
        
        # Software Section
        f.write("## SOFTWARE\n\n")
        f.write("### Python\n")
        f.write(f"- **Version**: {RESULTS['software']['python']['version']}\n")
        f.write(f"- **Path**: {RESULTS['software']['python']['path']}\n\n")
        
        f.write("### Node.js\n")
        f.write(f"- **Version**: {RESULTS['software']['nodejs']['version']}\n")
        f.write(f"- **NPM Version**: {RESULTS['software']['nodejs']['npm_version']}\n")
        f.write(f"- **Path**: {RESULTS['software']['nodejs']['path']}\n\n")
        
        f.write("### Git\n")
        f.write(f"- **Version**: {RESULTS['software']['git']}\n\n")
        
        f.write("### Docker\n")
        f.write(f"- **Version**: {RESULTS['software']['docker']['version']}\n")
        f.write(f"- **Compose**: {RESULTS['software']['docker']['compose']}\n\n")
        f.write("**Docker Images**:\n```\n")
        f.write(RESULTS["software"]["docker"].get("images", "None") + "\n```\n\n")
        
        f.write("### CUDA\n")
        f.write(f"- **Version**: {RESULTS['software']['cuda'] if RESULTS['software']['cuda'] else 'Not detected'}\n\n")
        
        f.write("### LLM Software\n")
        llm = RESULTS["software"].get("llm", {})
        f.write(f"- **llama.cpp**: {llm.get('llama_cpp', 'Not found')}\n")
        f.write(f"- **Ollama**: {llm.get('ollama', 'Not found')}\n")
        f.write(f"- **LM Studio**: {llm.get('lm_studio', 'Not found')}\n")
        f.write(f"- **Oobabooga**: {llm.get('oobabooga', 'Not found')}\n\n")
        
        # Python Packages
        f.write("### Python Packages\n\n")
        if RESULTS["python_packages"]:
            f.write("| Package | Version |\n")
            f.write("|---------|---------|\n")
            for pkg in RESULTS["python_packages"][:50]:  # First 50
                f.write(f"| {pkg.get('name', 'N/A')} | {pkg.get('version', 'N/A')} |\n")
            if len(RESULTS["python_packages"]) > 50:
                f.write(f"\n*... and {len(RESULTS['python_packages']) - 50} more packages*\n")
        else:
            f.write("*No packages listed or pip list failed*\n")
        f.write("\n")
        
        # Drive Space
        f.write("## DRIVE SPACE\n\n")
        for drive, info in RESULTS["drive_space"].items():
            f.write(f"### {drive}\n```\n{info}\n```\n\n")
        
        # GGUF Models Section
        f.write("## GGUF MODELS\n\n")
        if RESULTS["gguf_models"]:
            total_size = sum(m.get("size_bytes", 0) for m in RESULTS["gguf_models"] if "size_bytes" in m)
            f.write(f"**Total Models Found**: {len(RESULTS['gguf_models'])}\n\n")
            f.write(f"**Total Size**: {total_size / (1024**3):.2f} GB\n\n")
            
            f.write("### Model Inventory\n\n")
            f.write("| # | Filename | Size (GB) | Location |\n")
            f.write("|---|----------|-----------|----------|\n")
            
            for i, model in enumerate(RESULTS["gguf_models"], 1):
                filename = model.get("filename", "Unknown")
                size = model.get("size_gb", "N/A")
                directory = model.get("directory", "Unknown")
                f.write(f"| {i} | {filename} | {size} | {directory} |\n")
        else:
            f.write("*No GGUF models found on C:/ or D:/ drives*\n\n")
            f.write("### Recommended Download Locations\n\n")
            f.write("1. **Hugging Face**: https://huggingface.co/models?library=gguf\n")
            f.write("2. **TheBloke**: https://huggingface.co/TheBloke\n")
            f.write("3. **MaziyarPanahi**: https://huggingface.co/maziyarpanahi\n\n")
            f.write("### Recommended Models for This System\n\n")
            f.write("| Model | Size | Quant | Use Case |\n")
            f.write("|-------|------|-------|----------|\n")
            f.write("| Phi-3-mini | 2GB | Q4_K_M | Analyzer Agent |\n")
            f.write("| Llama-3.2-1B | 1GB | Q4_K_M | Deploy Agent |\n")
            f.write("| Mistral-7B-v0.3 | 4GB | Q4_K_M | Master Agent |\n")
            f.write("| Gemma-2-9B | 6GB | Q4_K_M | Complex Analysis |\n")
        
        # Summary
        f.write("\n---\n\n")
        f.write("## SYSTEM CAPABILITIES SUMMARY\n\n")
        
        # Determine GPU capability
        gpu_text = RESULTS["hardware"].get("gpu", "")
        has_nvidia = "NVIDIA" in gpu_text.upper()
        has_amd = "AMD" in gpu_text.upper() or "RADEON" in gpu_text.upper()
        has_intel = "INTEL" in gpu_text.upper()
        
        f.write("### AI/ML Readiness\n\n")
        if has_nvidia:
            f.write("✅ **NVIDIA GPU Detected** - CUDA acceleration available\n")
            f.write("   - Install: `CMAKE_ARGS=\"-DGGML_CUDA=on\" pip install llama-cpp-python`\n")
        elif has_amd:
            f.write("⚠️ **AMD GPU Detected** - ROCm support may be limited on Windows\n")
            f.write("   - Consider using DirectML or CPU-only mode\n")
        elif has_intel:
            f.write("⚠️ **Intel GPU Detected** - Limited GPU acceleration support\n")
            f.write("   - CPU mode recommended, or try OpenVINO\n")
        else:
            f.write("❌ **No Dedicated GPU Detected** - CPU-only mode\n")
            f.write("   - Will work but slower for large models\n")
        
        f.write("\n### Recommended Configuration\n\n")
        f.write("```bash\n")
        f.write("# For CPU-only (works on all systems)\n")
        f.write("pip install llama-cpp-python\n\n")
        f.write("# For NVIDIA GPU (if detected)\n")
        f.write("CMAKE_ARGS=\"-DGGML_CUDA=on\" pip install llama-cpp-python\n\n")
        f.write("# Model paths to configure\n")
        for model in RESULTS["gguf_models"][:5]:
            f.write(f"# - {model.get('path', 'N/A')}\n")
        f.write("```\n")
        
        f.write("\n### Deployment Capacity\n\n")
        f.write("| Component | Status | Notes |\n")
        f.write("|-----------|--------|-------|\n")
        f.write(f"| Python | ✅ {RESULTS['software']['python']['version']} | Ready |\n")
        f.write(f"| Node.js | ✅ {RESULTS['software']['nodejs']['version']} | Ready |\n")
        f.write(f"| Docker | ✅ {RESULTS['software']['docker']['version']} | Ready |\n")
        f.write(f"| Git | ✅ {RESULTS['software']['git']} | Ready |\n")
        if RESULTS["gguf_models"]:
            f.write(f"| GGUF Models | ✅ {len(RESULTS['gguf_models'])} found | Ready |\n")
        else:
            f.write("| GGUF Models | ❌ None found | Download needed |\n")
        
        f.write("\n---\n\n")
        f.write("*This file was auto-generated. Run `python deep_system_scan.py` to update.*\n")
    
    print(f"\n[OK] Results saved to: {os.path.abspath(output_file)}")
    print(f"[OK] GGUF models found: {len(RESULTS['gguf_models'])}")
    
    # Also save JSON for programmatic access
    json_file = 'system_scan_results.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(f"[OK] JSON results saved to: {os.path.abspath(json_file)}")
    
    # Auto-update documentation
    print("\n" + "=" * 60)
    print("AUTO-UPDATING DOCUMENTATION...")
    print("=" * 60)
    try:
        from auto_update_docs import main as update_docs
        update_docs()
    except Exception as e:
        print(f"Note: Documentation update skipped ({e})")
        print("Run 'python auto_update_docs.py' manually to update docs")

if __name__ == "__main__":
    main()
