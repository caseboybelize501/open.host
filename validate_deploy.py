"""
Pre-Deployment Validation Workflow (Offline)
============================================
Tests projects locally BEFORE pushing to GitHub.

Validates:
1. requirements.txt - Syntax check (no network)
2. package.json - Valid JSON
3. Dockerfile - Syntax check, file references exist
4. render.yaml - Valid Blueprint syntax
"""
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

print("=" * 70)
print("PRE-DEPLOYMENT VALIDATION (OFFLINE)")
print("=" * 70)
print(f"Started: {datetime.now().isoformat()}")

# ============================================================================
# VALIDATORS
# ============================================================================
def validate_requirements(repo_path):
    """Check requirements.txt syntax"""
    req_file = Path(repo_path) / "requirements.txt"
    if not req_file.exists():
        return None, "No requirements.txt"
    
    errors = []
    with open(req_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Basic syntax check
            if not re.match(r'^[a-zA-Z0-9_-]+([><=!]+[0-9.]+)?', line):
                errors.append(f"Line {line_num}: Invalid syntax: {line}")
    
    return len(errors) == 0, errors

def validate_package_json(repo_path):
    """Check package.json is valid JSON"""
    pkg_file = Path(repo_path) / "package.json"
    if not pkg_file.exists():
        return None, "No package.json"
    
    try:
        with open(pkg_file, 'r') as f:
            data = json.load(f)
        if 'name' not in data:
            return False, ["Missing 'name' field"]
        return True, []
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]

def validate_dockerfile(repo_path):
    """Check Dockerfile syntax and file references"""
    dockerfile = Path(repo_path) / "Dockerfile"
    if not dockerfile.exists():
        return None, "No Dockerfile"
    
    errors = []
    with open(dockerfile, 'r') as f:
        content = f.read()
    
    if 'FROM' not in content:
        errors.append("Missing FROM instruction")
    
    # Check referenced files exist (skip multi-stage and globs)
    for match in re.finditer(r'COPY\s+(.+?)\s+', content) or re.finditer(r'COPY\s+(\S+)$', content, re.MULTILINE):
        ref_file = match.group(1).strip()
        # Skip multi-stage builds (--from=...)
        if ref_file.startswith('--from=') or ref_file.startswith('$'):
            continue
        # Skip globs with *
        if '*' in ref_file:
            continue
        # Skip . (current directory)
        if ref_file == '.':
            continue
        if not (Path(repo_path) / ref_file).exists():
            errors.append(f"COPY references non-existent file: {ref_file}")
    
    return len(errors) == 0, errors

def validate_render_yaml(repo_path):
    """Check render.yaml syntax"""
    render_file = Path(repo_path) / "render.yaml"
    if not render_file.exists():
        return None, "No render.yaml"
    
    errors = []
    with open(render_file, 'r') as f:
        content = f.read()
    
    if 'services:' not in content:
        errors.append("Missing 'services:' section")
    if '- type:' not in content:
        errors.append("Missing service type definition")
    
    return len(errors) == 0, errors

# ============================================================================
# MAIN
# ============================================================================
workspace = Path(r"D:/Users/CASE/projects")

repos_to_validate = [
    # Tier 1
    "daw", "dev.portfolio", "fpga.design", "git.initv3", "git.intelli",
    "gpt.code.debug", "legal", "ml.learn", "RAM", "tech.debt.code",
    # Tier 2
    "100marr", "cohesion", "dev.ops", "firm.soft", "GROWTH.ENG",
    "humble", "nft-stamps", "open.host", "SW.ENG.TEAM", "tldr",
    "twin", "UNICORN5", "version",
    # Tier 3
    "32GBVRAMTEST", "AGENTFORGE", "CINEMATIC3D-FRAMEWORK", "DSP-MIX-MASTER",
    "git.initv2", "NEXUSBOT", "PROMPTJSON", "purposeforge", "SHADERPILOT",
    "VDJ", "nemotronforge"
]

results = {'passed': [], 'failed': [], 'skipped': []}

for repo_name in repos_to_validate:
    repo_path = workspace / repo_name
    if not repo_path.exists():
        results['skipped'].append(f"{repo_name}: Path not found")
        continue
    
    print(f"\n[{repo_name}]")
    repo_errors = []
    
    ok, msg = validate_requirements(repo_path)
    if ok is True:
        print(f"  [OK] requirements.txt")
    elif ok is False:
        for err in msg:
            print(f"  [ERR] {err}")
            repo_errors.append(f"requirements.txt: {err}")
    
    ok, msg = validate_package_json(repo_path)
    if ok is True:
        print(f"  [OK] package.json")
    elif ok is False:
        for err in msg:
            print(f"  [ERR] {err}")
            repo_errors.append(f"package.json: {err}")
    
    ok, msg = validate_dockerfile(repo_path)
    if ok is True:
        print(f"  [OK] Dockerfile")
    elif ok is False:
        for err in msg:
            print(f"  [ERR] {err}")
            repo_errors.append(f"Dockerfile: {err}")
    
    ok, msg = validate_render_yaml(repo_path)
    if ok is True:
        print(f"  [OK] render.yaml")
    elif ok is False:
        for err in msg:
            print(f"  [ERR] {err}")
            repo_errors.append(f"render.yaml: {err}")
    
    if repo_errors:
        results['failed'].append(f"{repo_name}: {repo_errors}")
    else:
        results['passed'].append(repo_name)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
print(f"Passed:  {len(results['passed'])}/{len(repos_to_validate)}")
print(f"Failed:  {len(results['failed'])}/{len(repos_to_validate)}")
print(f"Skipped: {len(results['skipped'])}/{len(repos_to_validate)}")

if results['failed']:
    print("\nFAILED REPOS (fix before deploying):")
    for repo in results['failed']:
        print(f"  - {repo}")

print(f"\nCompleted: {datetime.now().isoformat()}")
sys.exit(0 if not results['failed'] else 1)
