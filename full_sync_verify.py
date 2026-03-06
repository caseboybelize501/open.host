"""
Complete GitHub Sync + GitHub Desktop Analysis
"""
import os
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USER = os.getenv('GITHUB_USERNAME', 'caseboybelize501')
LOCAL_PROJECTS = Path(os.getenv('LOCAL_PROJECTS', r"D:/Users/CASE/projects"))

import requests

headers = {'Authorization': f'token {GITHUB_TOKEN}'}

print("=" * 70)
print("COMPLETE GITHUB SYNC + DESKTOP ANALYSIS")
print("=" * 70)

# ============================================================================
# STEP 1: Fetch GitHub repos
# ============================================================================
print("\n[1/5] Fetching GitHub repositories...")
url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"[ERR] GitHub API error: {response.status_code}")
    exit(1)

github_repos = {r['name'].lower(): r for r in response.json()}
print(f"[OK] Found {len(github_repos)} repos on GitHub")

# ============================================================================
# STEP 2: Scan local projects
# ============================================================================
print("\n[2/5] Scanning local projects...")
local_projects = {}

for proj_dir in LOCAL_PROJECTS.iterdir():
    if not proj_dir.is_dir():
        continue
    if proj_dir.name.startswith('.') or proj_dir.name.startswith('_'):
        continue
    
    # Get git remote
    git_dir = proj_dir / '.git'
    remote_url = None
    if git_dir.exists():
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=proj_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                remote_url = result.stdout.strip()
        except:
            pass
    
    local_projects[proj_dir.name.lower()] = {
        'path': proj_dir,
        'original_name': proj_dir.name,
        'git_remote': remote_url,
        'has_git': git_dir.exists()
    }

print(f"[OK] Found {len(local_projects)} local projects")

# ============================================================================
# STEP 3: Check GitHub Desktop
# ============================================================================
print("\n[3/5] Checking GitHub Desktop...")

# GitHub Desktop stores repos in %APPDATA%\GitHub Desktop\storage\
appdata = Path(os.getenv('APPDATA', ''))
desktop_config = appdata / 'GitHub Desktop' / 'storage'

github_desktop_repos = []

if desktop_config.exists():
    print(f"[OK] GitHub Desktop config found: {desktop_config}")
    
    # Look for repositories.json
    repos_file = desktop_config / 'repositories.json'
    if repos_file.exists():
        try:
            with open(repos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                github_desktop_repos = data
                print(f"[OK] GitHub Desktop managing {len(github_desktop_repos)} repos")
            elif isinstance(data, dict) and 'repositories' in data:
                github_desktop_repos = data['repositories']
                print(f"[OK] GitHub Desktop managing {len(github_desktop_repos)} repos")
        except Exception as e:
            print(f"[WARN] Could not read repositories.json: {e}")
    else:
        print("[--] repositories.json not found")
else:
    print("[--] GitHub Desktop not installed or config not found")

# Check which local repos are in GitHub Desktop
desktop_paths = set()
for repo in github_desktop_repos:
    if isinstance(repo, dict) and 'path' in repo:
        desktop_paths.add(Path(repo['path']))

print("\nGitHub Desktop managed repos:")
for repo in github_desktop_repos[:10]:
    if isinstance(repo, dict):
        name = repo.get('name', 'Unknown')
        path = repo.get('path', 'Unknown')
        print(f"  - {name}: {path}")
if len(github_desktop_repos) > 10:
    print(f"  ... and {len(github_desktop_repos) - 10} more")

# ============================================================================
# STEP 4: Verify sync status
# ============================================================================
print("\n" + "=" * 70)
print("[4/5] VERIFYING SYNC STATUS")
print("=" * 70)

synced = []
case_diffs = []
missing_local = []
missing_github = []
remote_issues = []

for gh_name, gh_repo in github_repos.items():
    if gh_name in local_projects:
        local_info = local_projects[gh_name]
        
        # Check name case
        if gh_name != local_info['original_name'].lower():
            case_diffs.append({
                'github': gh_name,
                'local': local_info['original_name']
            })
        
        # Check git remote
        expected_remote = f"https://github.com/{GITHUB_USER}/{gh_name}.git"
        actual_remote = local_info.get('git_remote', '')
        
        if actual_remote:
            # Normalize remotes for comparison
            expected_normalized = expected_remote.lower().replace('https://', '').replace('http://', '')
            actual_normalized = actual_remote.lower().replace('https://', '').replace('http://', '')
            
            if expected_normalized != actual_normalized:
                remote_issues.append({
                    'name': gh_name,
                    'expected': expected_remote,
                    'actual': actual_remote
                })
        
        synced.append(gh_name)
    else:
        missing_local.append(gh_name)

for local_name in local_projects.keys():
    if local_name not in github_repos:
        missing_github.append(local_name)

print(f"\nSync Results:")
print(f"  Synced (GitHub + Local): {len(synced)}")
print(f"  Case differences: {len(case_diffs)}")
print(f"  Remote URL issues: {len(remote_issues)}")
print(f"  Missing locally: {len(missing_local)}")
print(f"  Missing on GitHub: {len(missing_github)}")

# ============================================================================
# STEP 5: Fix case sensitivity (optional)
# ============================================================================
print("\n" + "=" * 70)
print("[5/5] CASE SENSITIVITY FIX")
print("=" * 70)

if case_diffs:
    print(f"\n{len(case_diffs)} projects have different casing:")
    
    for diff in case_diffs[:15]:
        print(f"  GitHub: {diff['github']}")
        print(f"  Local:  {diff['local']}")
    
    if len(case_diffs) > 15:
        print(f"  ... and {len(case_diffs) - 15} more")
    
    print("\nNote: Windows is case-insensitive, so this doesn't affect local work.")
    print("      But matching GitHub casing helps with Git operations.")
else:
    print("\n[OK] All project names match GitHub casing!")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("SYNC VERIFICATION COMPLETE")
print("=" * 70)

print(f"""
SUMMARY:
  GitHub Repositories: {len(github_repos)}
  Local Projects: {len(local_projects)}
  Fully Synced: {len(synced)}
  GitHub Desktop Managed: {len(github_desktop_repos)}

STATUS:
  Case Differences: {len(case_diffs)} (cosmetic on Windows)
  Remote Issues: {len(remote_issues)}
  Missing Locally: {len(missing_local)}
  Missing on GitHub: {len(missing_github)}

DEPLOYMENT READY:
""")

# Count deployment-ready
deploy_ready = 0
for name in synced:
    proj_path = local_projects[name]['path']
    if (proj_path / 'Dockerfile').exists() or (proj_path / 'render.yaml').exists():
        deploy_ready += 1

print(f"  Projects with Dockerfile/render.yaml: {deploy_ready}")

if remote_issues:
    print("\nREMOTE URL ISSUES (may need fixing):")
    for issue in remote_issues[:5]:
        print(f"  - {issue['name']}")
        print(f"    Expected: {issue['expected']}")
        print(f"    Actual: {issue['actual']}")

print("\n" + "=" * 70)
