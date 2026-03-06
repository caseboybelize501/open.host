"""
Open.Host Jarvis - Local Build Workflow
========================================
1. Scan GitHub for profitable repos
2. Clone to local workspace (D:/projects or similar)
3. Build and test offline
4. Deploy to free/open hosting when ready
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
USERNAME = os.getenv('GITHUB_USERNAME', 'caseboybelize501')
WORKSPACE_BASE = os.getenv('WORKSPACE_BASE', 'D:/projects/open-host-workspace')

print("=" * 70)
print("OPEN.HOST JARVIS - LOCAL BUILD WORKFLOW")
print("=" * 70)

print(f"\nConfiguration:")
print(f"  GitHub User: {USERNAME}")
print(f"  Token: {'[CONFIGURED]' if GITHUB_TOKEN else '[MISSING]'}")
print(f"  Workspace: {WORKSPACE_BASE}")

# Create workspace
workspace = Path(WORKSPACE_BASE)
workspace.mkdir(parents=True, exist_ok=True)
print(f"  Workspace exists: {workspace.exists()}")

# ============================================================================
# STEP 1: SCAN GITHUB
# ============================================================================
print("\n" + "=" * 70)
print("STEP 1: SCAN GITHUB FOR PROFITABLE REPOS")
print("=" * 70)

import requests

headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}

url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"
response = requests.get(url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"[ERR] GitHub API error: {response.status_code}")
    exit(1)

repos = response.json()
print(f"[OK] Found {len(repos)} repositories")

# Analyze and score
print("\nAnalyzing repositories...")
for repo in repos:
    if repo.get('fork') or repo.get('archived'):
        repo['profit_score'] = 0
        continue
    
    score = 0.0
    
    # Recent activity
    updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
    days_old = (datetime.now(updated.tzinfo) - updated).days
    if days_old < 7: score += 3.0
    elif days_old < 30: score += 2.0
    
    # Has package files
    contents_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/contents"
    contents_resp = requests.get(contents_url, headers=headers, timeout=5)
    if contents_resp.status_code == 200:
        contents = contents_resp.json()
        files = [f['name'] for f in contents] if isinstance(contents, list) else []
        
        if 'package.json' in files: score += 2.0
        if 'requirements.txt' in files: score += 2.0
        if 'index.html' in files: score += 1.0
        if 'README.md' in files: score += 1.0
    
    repo['profit_score'] = min(score, 10.0)
    repo['days_old'] = days_old

# Sort and filter
profitable = [r for r in repos if r.get('profit_score', 0) >= 5.0]
profitable.sort(key=lambda x: x['profit_score'], reverse=True)

print(f"[OK] Profitable repos (score >= 5.0): {len(profitable)}")

# Show top 10
print("\nTop 10 Profitable Repos:")
for i, repo in enumerate(profitable[:10], 1):
    print(f"  {i:2}. {repo['name']:30} Score: {repo['profit_score']:.1f} | Updated: {repo['days_old']}d ago")

# ============================================================================
# STEP 2: SELECT REPOS TO CLONE
# ============================================================================
print("\n" + "=" * 70)
print("STEP 2: SELECT REPOS TO CLONE LOCALLY")
print("=" * 70)

# Auto-select top 5 if no args
selected_numbers = []
if len(sys.argv) > 1:
    try:
        selected_numbers = [int(x) for x in sys.argv[1].split(',')]
    except:
        pass

if selected_numbers:
    selected_repos = [profitable[i-1] for i in selected_numbers if 0 < i <= len(profitable)]
else:
    # Auto-select top 5
    selected_repos = profitable[:5]

print(f"\nSelected {len(selected_repos)} repos for local cloning:")
for i, repo in enumerate(selected_repos, 1):
    print(f"  {i}. {repo['name']} (Score: {repo['profit_score']:.1f})")

# ============================================================================
# STEP 3: CLONE TO LOCAL WORKSPACE
# ============================================================================
print("\n" + "=" * 70)
print("STEP 3: CLONE REPOS TO LOCAL WORKSPACE")
print("=" * 70)

cloned_repos = []

for repo in selected_repos:
    repo_name = repo['name']
    repo_url = repo['clone_url']
    local_path = workspace / repo_name
    
    print(f"\n[{repo_name}]")
    
    if local_path.exists():
        print(f"  [EXISTS] {local_path}")
        print(f"  -> Pulling latest changes...")
        
        try:
            subprocess.run(['git', 'pull'], cwd=local_path, capture_output=True, timeout=30)
            print(f"  [OK] Pulled latest")
        except Exception as e:
            print(f"  [WARN] Pull failed: {e}")
        
        cloned_repos.append({
            'name': repo_name,
            'path': local_path,
            'url': repo_url,
            'score': repo['profit_score']
        })
    else:
        print(f"  [NEW] Cloning to {local_path}...")
        
        try:
            subprocess.run(
                ['git', 'clone', repo_url, str(local_path)],
                capture_output=True,
                timeout=60
            )
            print(f"  [OK] Cloned successfully")
            
            cloned_repos.append({
                'name': repo_name,
                'path': local_path,
                'url': repo_url,
                'score': repo['profit_score']
            })
        except Exception as e:
            print(f"  [ERR] Clone failed: {e}")

print(f"\n[OK] Cloned {len(cloned_repos)} repositories to workspace")

# ============================================================================
# STEP 4: ANALYZE LOCAL PROJECTS
# ============================================================================
print("\n" + "=" * 70)
print("STEP 4: ANALYZE LOCAL PROJECTS")
print("=" * 70)

for repo in cloned_repos:
    print(f"\n{'='*60}")
    print(f"PROJECT: {repo['name']}")
    print(f"Path: {repo['path']}")
    print(f"Score: {repo['score']:.1f}/10")
    print(f"{'='*60}")
    
    path = repo['path']
    
    # Check for project files
    files = list(path.glob('*'))
    file_names = [f.name for f in files]
    
    print(f"\nFiles found: {len(files)}")
    
    # Detect project type
    project_types = []
    
    if (path / 'package.json').exists():
        project_types.append('Node.js')
        print("  [OK] package.json found (Node.js)")
        
        # Check framework
        if (path / 'next.config.js').exists() or (path / 'next.config.ts').exists():
            project_types.append('Next.js')
            print("  [OK] Next.js detected")
        elif (path / 'vite.config.js').exists() or (path / 'vite.config.ts').exists():
            project_types.append('Vite')
            print("  [OK] Vite detected")
        elif (path / 'nuxt.config.js').exists():
            project_types.append('Nuxt')
            print("  [OK] Nuxt detected")
    
    if (path / 'requirements.txt').exists():
        project_types.append('Python')
        print("  [OK] requirements.txt found (Python)")
    
    if (path / 'index.html').exists():
        project_types.append('Static Site')
        print("  [OK] index.html found (Static Site)")
    
    if (path / 'Cargo.toml').exists():
        project_types.append('Rust')
        print("  [OK] Cargo.toml found (Rust)")
    
    if (path / 'go.mod').exists():
        project_types.append('Go')
        print("  [OK] go.mod found (Go)")
    
    # Recommend platform
    print(f"\nProject Type: {', '.join(project_types) or 'Unknown'}")
    
    if 'Next.js' in project_types or 'React' in project_types:
        print("Recommended Platform: Vercel (free tier)")
    elif 'Nuxt' in project_types or 'Vue' in project_types:
        print("Recommended Platform: Netlify or Vercel (free tier)")
    elif 'Static Site' in project_types:
        print("Recommended Platform: GitHub Pages, Netlify, or Vercel (all free)")
    elif 'Python' in project_types:
        print("Recommended Platform: Render (free tier)")
    elif 'Rust' in project_types:
        print("Recommended Platform: Render (free tier)")
    else:
        print("Recommended Platform: Depends on build output")

# ============================================================================
# STEP 5: NEXT STEPS
# ============================================================================
print("\n" + "=" * 70)
print("WORKSPACE READY - NEXT STEPS")
print("=" * 70)

print(f"""
Workspace: {workspace}

You can now:

1. BUILD LOCALLY
   cd {workspace}/<repo-name>
   npm install && npm run build    # Node.js
   pip install -r requirements.txt # Python

2. TEST LOCALLY
   npm run dev    # Development server
   npm run test   # Run tests

3. DEPLOY WHEN READY (Free Hosting Options)
   - GitHub Pages: Free for static sites
   - Netlify: 100GB/month free
   - Vercel: 100GB/month free
   - Render: Unlimited bandwidth free tier

4. CONTINUE DEVELOPMENT
   - Make changes locally
   - Commit and push to GitHub
   - Re-run this workflow to sync

Commands:
  git status          # Check local changes
  git pull            # Sync from GitHub
  git push            # Push local changes
""")

# Save workspace manifest
manifest_path = workspace / 'workspace_manifest.txt'
with open(manifest_path, 'w') as f:
    f.write("OPEN.HOST JARVIS - WORKSPACE MANIFEST\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Created: {datetime.now().isoformat()}\n")
    f.write(f"GitHub User: {USERNAME}\n")
    f.write(f"Workspace: {workspace}\n\n")
    f.write("CLONED REPOSITORIES:\n")
    f.write("-" * 50 + "\n\n")
    
    for repo in cloned_repos:
        f.write(f"{repo['name']}\n")
        f.write(f"  Path: {repo['path']}\n")
        f.write(f"  URL: {repo['url']}\n")
        f.write(f"  Score: {repo['score']:.1f}\n\n")

print(f"[OK] Workspace manifest saved to: {manifest_path}")
print("\n" + "=" * 70)
