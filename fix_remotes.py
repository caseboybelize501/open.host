"""
Fix Git Remote URLs - Remove token from URLs and fix case
"""
import os
import subprocess
from pathlib import Path

GITHUB_USER = 'caseboybelize501'
LOCAL_PROJECTS = Path(r"D:/Users/CASE/projects")

print("=" * 70)
print("FIXING GIT REMOTE URLS")
print("=" * 70)

fixed = 0
errors = 0

for proj_dir in LOCAL_PROJECTS.iterdir():
    if not proj_dir.is_dir():
        continue
    if proj_dir.name.startswith('.') or proj_dir.name.startswith('_'):
        continue
    
    git_dir = proj_dir / '.git'
    if not git_dir.exists():
        continue
    
    # Get current remote
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=proj_dir,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            continue
        
        current_url = result.stdout.strip()
        
        # Check if URL has token in it
        if 'ghp_' in current_url or proj_dir.name.upper() in current_url:
            # Fix the URL (clean, no token, correct case)
            clean_url = f"https://github.com/{GITHUB_USER}/{proj_dir.name}.git"
            
            # Set new remote URL
            subprocess.run(
                ['git', 'remote', 'set-url', 'origin', clean_url],
                cwd=proj_dir,
                capture_output=True,
                timeout=5
            )
            
            print(f"[FIXED] {proj_dir.name}")
            print(f"  Old: {current_url[:80]}...")
            print(f"  New: {clean_url}")
            fixed += 1
    except Exception as e:
        errors += 1

print("\n" + "=" * 70)
print(f"COMPLETE: {fixed} fixed, {errors} errors")
print("=" * 70)
