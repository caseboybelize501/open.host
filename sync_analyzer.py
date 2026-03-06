"""
GitHub <-> Local Sync Analyzer
Matches local projects with GitHub repos and shows deployment readiness
"""
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_USER = os.getenv('GITHUB_USERNAME', 'caseboybelize501')
LOCAL_PROJECTS = Path(r"D:/Users/CASE/projects")

headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

print("=" * 70)
print("GITHUB <-> LOCAL SYNC ANALYZER")
print("=" * 70)

# Fetch GitHub repos
print("\nFetching GitHub repos...")
url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"[ERR] GitHub API error: {response.status_code}")
    exit(1)

github_repos = {r['name']: r for r in response.json()}
print(f"[OK] Found {len(github_repos)} repos on GitHub")

# Scan local projects
print(f"\nScanning local projects in {LOCAL_PROJECTS}...")
local_projects = {}

for proj_dir in LOCAL_PROJECTS.iterdir():
    if not proj_dir.is_dir():
        continue
    if proj_dir.name.startswith('.') or proj_dir.name.startswith('_'):
        continue
    
    # Check deployment files
    has_docker = (proj_dir / 'Dockerfile').exists()
    has_render = (proj_dir / 'render.yaml').exists()
    has_package = (proj_dir / 'package.json').exists()
    has_requirements = (proj_dir / 'requirements.txt').exists()
    has_git = (proj_dir / '.git').exists()
    
    local_projects[proj_dir.name] = {
        'path': proj_dir,
        'dockerfile': has_docker,
        'render_yaml': has_render,
        'package_json': has_package,
        'requirements': has_requirements,
        'git': has_git
    }

print(f"[OK] Found {len(local_projects)} local projects")

# Match and analyze
print("\n" + "=" * 70)
print("SYNC STATUS")
print("=" * 70)

matched = []
local_only = []
github_only = []

for name, local_info in local_projects.items():
    if name in github_repos:
        matched.append(name)
    else:
        local_only.append(name)

for name in github_repos.keys():
    if name not in local_projects:
        github_only.append(name)

print(f"\nMatched (Local + GitHub): {len(matched)}")
print(f"Local Only: {len(local_only)}")
print(f"GitHub Only: {len(github_only)}")

# Show deployment-ready projects
print("\n" + "=" * 70)
print("DEPLOYMENT READY (Has Dockerfile or render.yaml)")
print("=" * 70)

ready_projects = []

for name, info in local_projects.items():
    if info['dockerfile'] or info['render_yaml']:
        in_github = name in github_repos
        ready_projects.append({
            'name': name,
            'dockerfile': info['dockerfile'],
            'render_yaml': info['render_yaml'],
            'in_github': in_github,
            'github_url': github_repos.get(name, {}).get('html_url', '')
        })

ready_projects.sort(key=lambda x: (x['in_github'], x['dockerfile']), reverse=True)

for proj in ready_projects[:25]:
    status = "[GH+LOCAL]" if proj['in_github'] else "[LOCAL ONLY]"
    files = []
    if proj['dockerfile']: files.append("Dockerfile")
    if proj['render_yaml']: files.append("render.yaml")
    
    print(f"\n{proj['name']} {status}")
    print(f"  Deploy Files: {', '.join(files)}")
    if proj['in_github']:
        print(f"  GitHub: {proj['github_url']}")
        print(f"  -> Deploy: https://dashboard.render.com -> Connect '{proj['name']}'")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"""
Total Local Projects: {len(local_projects)}
Total GitHub Repos: {len(github_repos)}
Synced: {len(matched)}
Deployment Ready: {len(ready_projects)}

TO DEPLOY:
1. Pick a project from the "DEPLOYMENT READY" list
2. Go to https://dashboard.render.com
3. New + -> Blueprint
4. Connect GitHub repo: caseboybelize501/<project-name>
5. Deploy!

FREE HOSTING OPTIONS:
- Render: https://render.com (750 hrs/month free)
- Vercel: https://vercel.com (100GB/month free)
- Railway: https://railway.app ($5 credit/month)
- Fly.io: https://fly.io (3 shared VMs free)
""")

print("=" * 70)
