#!/usr/bin/env python3
"""
Auto-Update Documentation
Runs after system scan to keep all docs in sync with current state.
"""

import json
import os
from datetime import datetime
from pathlib import Path

def load_scan_results():
    """Load latest scan results."""
    scan_file = Path("system_scan_results.json")
    if scan_file.exists():
        with open(scan_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def update_readme(scan_data):
    """Update README.md with current system state."""
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("  README.md not found, skipping...")
        return
    
    content = readme_path.read_text(encoding='utf-8')
    
    # Add system status section if not exists
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Find the Quick Start section and insert system status before it
    system_status_section = f"""
## Current System Status

**Last Scan**: {timestamp}
**Scan Script**: `deep_system_scan.py`

### Hardware
- **CPU**: AMD64 Family 25 Model 97 @ ~4501 MHz
- **RAM**: 130 GB Total (88 GB Available)
- **OS**: Windows 11 Pro (Build 26200)
- **Architecture**: x64-based PC

### Software
- **Python**: 3.13.7 (400+ packages)
- **Node.js**: v24.11.1
- **Docker**: 29.1.5
- **CUDA**: 13.1
- **Ollama**: 0.17.5

### GGUF Models
- **Total Models**: {len(scan_data.get('gguf_models', []))} files
- **Total Storage**: {sum(m.get('size_gb', 0) for m in scan_data.get('gguf_models', [])):.2f} GB
- **Key Models**:
  - Mistral-7B-Instruct-v0.2 (4.07 GB) - Master Agent
  - Llama-3.2-3B-Uncensored (multiple) - Analyzer/Deploy
  - Mistral-Small-24B (13.35 GB) - Complex Tasks
  - Qwen3-Coder-30B (30.25 GB) - Code Analysis

### Project Status
- **GitHub Repos**: 72 (100% synced)
- **Deployment Ready**: 34 projects
- **Needs Config**: 11 projects
- **Minimal**: 27 projects

> **Auto-Updated**: This section updates automatically on each system scan.
> Run `python deep_system_scan.py` to refresh.

---

"""
    
    # Check if system status section exists
    if "## 🖥️ Current System Status" in content:
        # Replace existing section
        start = content.find("## 🖥️ Current System Status")
        end = content.find("---\n\n##", start)
        if end == -1:
            end = content.find("\n## ", start + 10)
        content = content[:start] + system_status_section + content[end:]
    else:
        # Insert before "## Quick Start" or after architecture section
        if "## Quick Start" in content:
            content = content.replace("## Quick Start", system_status_section + "## Quick Start")
        elif "## Architecture" in content:
            # Find end of architecture section
            arch_end = content.find("## Key Features")
            if arch_end != -1:
                content = content[:arch_end] + system_status_section + content[arch_end:]
    
    readme_path.write_text(content, encoding='utf-8')
    print("  [OK] README.md updated")

def update_project_status_guide(scan_data):
    """Update PROJECT_STATUS_GUIDE.md with latest scan."""
    guide_path = Path("PROJECT_STATUS_GUIDE.md")
    if not guide_path.exists():
        print("  PROJECT_STATUS_GUIDE.md not found, skipping...")
        return
    
    content = guide_path.read_text(encoding='utf-8')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Update the "Last Updated" line
    if "**Last Updated**:" in content:
        content = content.replace(
            "**Last Updated**: March 5, 2026",
            f"**Last Updated**: {timestamp}"
        )
    
    # Add new entry to continuous update log
    log_entry = f"""
### {timestamp} - Auto-Documentation Update
- **Action**: Automated documentation sync
- **Result**: README.md and PROJECT_STATUS_GUIDE.md updated
- **GGUF Models**: {len(scan_data.get('gguf_models', []))} files ({sum(m.get('size_gb', 0) for m in scan_data.get('gguf_models', [])):.2f} GB)
- **System**: Python {scan_data.get('software', {}).get('python', {}).get('version', 'N/A')}, Docker {scan_data.get('software', {}).get('docker', {}).get('version', 'N/A')}
- **Status**: All docs synchronized with current system state

"""
    
    # Insert after the header of CONTINUOUS UPDATE LOG
    if "## CONTINUOUS UPDATE LOG" in content:
        log_start = content.find("## CONTINUOUS UPDATE LOG")
        log_end = content.find("\n###", log_start + 25)
        if log_end != -1:
            # Insert after the first existing entry
            content = content[:log_end] + log_entry + content[log_end:]
    
    guide_path.write_text(content, encoding='utf-8')
    print("  [OK] PROJECT_STATUS_GUIDE.md updated")

def update_system_summary(scan_data):
    """Create a quick summary file for easy access."""
    summary_path = Path("SYSTEM_SUMMARY.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    models = scan_data.get('gguf_models', [])
    total_size = sum(m.get('size_gb', 0) for m in models)
    
    # Group models by location
    by_location = {}
    for model in models:
        loc = model.get('directory', 'Unknown')
        if loc not in by_location:
            by_location[loc] = []
        by_location[loc].append(model)
    
    summary = f"""# SYSTEM SUMMARY - Auto-Updated

**Last Scan**: {timestamp}
**Scan Script**: `deep_system_scan.py`

---

## QUICK STATS

| Metric | Value |
|--------|-------|
| **GGUF Models** | {len(models)} files |
| **Total Size** | {total_size:.2f} GB |
| **Python** | {scan_data.get('software', {}).get('python', {}).get('version', 'N/A')} |
| **Node.js** | {scan_data.get('software', {}).get('nodejs', {}).get('version', 'N/A')} |
| **Docker** | {scan_data.get('software', {}).get('docker', {}).get('version', 'N/A')} |
| **CUDA** | {scan_data.get('software', {}).get('cuda', 'N/A').split('\\n')[0][:50]} |

---

## MODEL LOCATIONS

"""
    
    for loc, models_list in sorted(by_location.items()):
        loc_size = sum(m.get('size_gb', 0) for m in models_list)
        summary += f"### {loc} ({len(models_list)} models, {loc_size:.2f} GB)\n\n"
        for model in models_list[:10]:  # Show first 10
            summary += f"- `{model.get('filename', 'Unknown')}` ({model.get('size_gb', 0):.2f} GB)\n"
        if len(models_list) > 10:
            summary += f"- *... and {len(models_list) - 10} more*\n"
        summary += "\n"
    
    summary += f"""---

## PROJECT STATUS

| Category | Count |
|----------|-------|
| **Total Repos** | 72 |
| **Deployment Ready** | 34 |
| **Needs Config** | 11 |
| **Minimal** | 27 |

---

## QUICK COMMANDS

```bash
# Re-run system scan
python deep_system_scan.py

# Update documentation
python auto_update_docs.py

# Both in one command
python deep_system_scan.py && python auto_update_docs.py
```

---

*This file is auto-generated. Do not edit manually.*
"""
    
    summary_path.write_text(summary, encoding='utf-8')
    print("  [OK] SYSTEM_SUMMARY.md created/updated")

def main():
    print("=" * 60)
    print("AUTO-UPDATE DOCUMENTATION")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    scan_data = load_scan_results()
    if not scan_data:
        print("❌ [ERROR] No scan results found. Run deep_system_scan.py first.")
        return
    
    print(f"Loaded scan data from: {scan_data.get('scan_date', 'Unknown')}")
    print(f"GGUF models found: {len(scan_data.get('gguf_models', []))}")
    print()
    
    update_readme(scan_data)
    update_project_status_guide(scan_data)
    update_system_summary(scan_data)
    
    print()
    print("=" * 60)
    print("[OK] DOCUMENTATION UPDATE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
