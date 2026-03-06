"""
Sync GitHub repos to local D:/Users/CASE/projects
Clones any GitHub repos that aren't locally
"""
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_USER = os.getenv('GITHUB_USERNAME', 'caseboybelize501')
LOCAL_PROJECTS = Path(r"D:/Users/CASE/projects")

import requests

headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

print("=" * 70)
print("GITHUB -> LOCAL SYNC")
print("=" * 70)

# Fetch GitHub repos
print("\nFetching GitHub repos...")
url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"[ERR] GitHub API error: {response.status_code}")
    exit(1)

github_repos = [r['name'] for r in response.json()]
print(f"[OK] Found {len(github_repos)} repos on GitHub")

# Check local
local_projects = set()
for proj_dir in LOCAL_PROJECTS.iterdir():
    if proj_dir.is_dir() and not proj_dir.name.startswith('.') and not proj_dir.name.startswith('_'):
        local_projects.add(proj_dir.name)

print(f"[OK] Found {len(local_projects)} local projects")

# Find missing
github_only = set(github_repos) - local_projects
local_only = local_projects - set(github_repos)

print(f"\nSync Status:")
print(f"  On GitHub only: {len(github_only)}")
print(f"  Local only: {len(local_only)}")

# Clone missing repos
if github_only:
    print("\n" + "=" * 70)
    print(f"CLONING {len(github_only)} MISSING REPOS")
    print("=" * 70)
    
    cloned = 0
    failed = 0
    
    for repo_name in sorted(github_only):
        repo_path = LOCAL_PROJECTS / repo_name
        
        if repo_path.exists():
            print(f"[SKIP] {repo_name} (already exists)")
            continue
        
        print(f"\n[{cloned+1}/{len(github_only)}] Cloning {repo_name}...")
        
        try:
            clone_url = f"https://github.com/{GITHUB_USER}/{repo_name}.git"
            subprocess.run(
                ['git', 'clone', clone_url, str(repo_path)],
                capture_output=True,
                timeout=60,
                check=True
            )
            print(f"  [OK] Cloned to {repo_path}")
            cloned += 1
        except Exception as e:
            print(f"  [ERR] Failed: {e}")
            failed += 1
    
    print(f"\n" + "=" * 70)
    print(f"CLONE COMPLETE: {cloned} cloned, {failed} failed")
    print("=" * 70)
else:
    print("\n[OK] All GitHub repos are synced locally!")

# Show local-only (not on GitHub)
if local_only:
    print("\n" + "=" * 70)
    print("LOCAL ONLY (not on GitHub)")
    print("=" * 70)
    print("These exist locally but not on GitHub:")
    for name in sorted(local_only)[:20]:
        print(f"  - {name}")
    if len(local_only) > 20:
        print(f"  ... and {len(local_only) - 20} more")

print("\n" + "=" * 70)
print("SYNC STATUS")
print("=" * 70)

# Re-check
local_projects_after = set()
for proj_dir in LOCAL_PROJECTS.iterdir():
    if proj_dir.is_dir() and not proj_dir.name.startswith('.') and not proj_dir.name.startswith('_'):
        local_projects_after.add(proj_dir.name)

github_set = set(github_repos)
synced = github_set & local_projects_after

print(f"""
GitHub Repos: {len(github_set)}
Local Projects: {len(local_projects_after)}
Synced (Both): {len(synced)}
Missing Locally: {len(github_set - local_projects_after)}
Local Only: {len(local_projects_after - github_set)}

Sync Complete: {'YES' if len(github_set - local_projects_after) == 0 else 'NO'}
""")

print("=" * 70)
