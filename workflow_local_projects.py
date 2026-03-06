"""
Open.Host Jarvis - Local Project Workflow
Works with existing D:/Users/CASE/projects structure
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Configuration
PROJECTS_ROOT = Path(r"D:/Users/CASE/projects")
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'caseboybelize501')

print("=" * 70)
print("OPEN.HOST JARVIS - LOCAL PROJECT WORKFLOW")
print("=" * 70)
print(f"\nProjects Root: {PROJECTS_ROOT}")
print(f"GitHub User: {GITHUB_USERNAME}")

# Check if projects root exists
if not PROJECTS_ROOT.exists():
    print(f"[ERR] Projects root not found: {PROJECTS_ROOT}")
    sys.exit(1)

# Scan for projects with deployment configs
print("\n" + "=" * 70)
print("SCANNING FOR DEPLOYABLE PROJECTS")
print("=" * 70)

deployable_projects = []

for project_dir in PROJECTS_ROOT.iterdir():
    if not project_dir.is_dir():
        continue
    
    if project_dir.name.startswith('.') or project_dir.name.startswith('_'):
        continue
    
    # Check for deployment indicators
    has_package_json = (project_dir / 'package.json').exists()
    has_requirements = (project_dir / 'requirements.txt').exists()
    has_dockerfile = (project_dir / 'Dockerfile').exists()
    has_render_yaml = (project_dir / 'render.yaml').exists()
    has_readme = (project_dir / 'README.md').exists()
    
    # Calculate deployability score
    score = 0
    indicators = []
    
    if has_package_json:
        score += 2
        indicators.append('package.json')
    if has_requirements:
        score += 2
        indicators.append('requirements.txt')
    if has_dockerfile:
        score += 3
        indicators.append('Dockerfile')
    if has_render_yaml:
        score += 3
        indicators.append('render.yaml')
    if has_readme:
        score += 1
        indicators.append('README.md')
    
    if score >= 4:  # At least 2 indicators
        deployable_projects.append({
            'name': project_dir.name,
            'path': project_dir,
            'score': score,
            'indicators': indicators,
            'has_package_json': has_package_json,
            'has_requirements': has_requirements,
            'has_dockerfile': has_dockerfile,
            'has_render_yaml': has_render_yaml
        })

# Sort by score
deployable_projects.sort(key=lambda x: x['score'], reverse=True)

print(f"\nFound {len(deployable_projects)} deployable projects")

# Show top projects
print("\n" + "=" * 70)
print("TOP DEPLOYABLE PROJECTS")
print("=" * 70)

for i, proj in enumerate(deployable_projects[:20], 1):
    print(f"\n{i}. {proj['name']}")
    print(f"   Score: {proj['score']}/10")
    print(f"   Indicators: {', '.join(proj['indicators'])}")
    
    # Recommend platform
    if proj['has_render_yaml']:
        print(f"   -> Ready for Render deployment")
    elif proj['has_dockerfile']:
        print(f"   -> Docker-ready (Render/Fly.io/Railway)")
    elif proj['has_package_json'] and not proj['has_requirements']:
        print(f"   -> Node.js (Vercel/Netlify)")
    elif proj['has_requirements']:
        print(f"   -> Python (Render/Railway)")

# Detailed view of top 3
print("\n" + "=" * 70)
print("DETAILED VIEW - TOP 3 PROJECTS")
print("=" * 70)

for proj in deployable_projects[:3]:
    print(f"\n{'='*60}")
    print(f"PROJECT: {proj['name']}")
    print(f"{'='*60}")
    print(f"Path: {proj['path']}")
    print(f"Score: {proj['score']}/10")
    
    # Check git status
    git_dir = proj['path'] / '.git'
    if git_dir.exists():
        print(f"Git: [OK] Initialized")
    else:
        print(f"Git: [--] Not initialized")
    
    # Show files
    files = list(proj['path'].glob('*'))
    file_count = len([f for f in files if f.is_file()])
    dir_count = len([f for f in files if f.is_dir()])
    print(f"Files: {file_count} files, {dir_count} directories")
    
    # Deployment readiness
    print(f"\nDeployment Readiness:")
    if proj['has_render_yaml']:
        print(f"  READY - Has render.yaml")
        print(f"     Deploy: https://dashboard.render.com -> New + -> Blueprint")
    elif proj['has_dockerfile']:
        print(f"  READY - Has Dockerfile")
        print(f"     Deploy: Render, Fly.io, or Railway")
    elif proj['has_package_json'] or proj['has_requirements']:
        print(f"  NEEDS CONFIG - Add render.yaml or Dockerfile")
        print(f"     Run: python add_deploy_config.py {proj['name']}")
    else:
        print(f"  NOT READY - Missing deployment files")

# Summary
print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)

ready_count = len([p for p in deployable_projects if p['has_render_yaml'] or p['has_dockerfile']])
needs_config_count = len([p for p in deployable_projects if not p['has_render_yaml'] and not p['has_dockerfile']])

print(f"""
Summary:
  Total Projects: {len(list(PROJECTS_ROOT.iterdir())) - 2}
  Deployable: {len(deployable_projects)}
  Ready to Deploy: {ready_count}
  Need Config: {needs_config_count}

Actions:
  1. Deploy ready projects:
     - Go to render.com or vercel.com
     - Connect GitHub repo
     - Deploy!

  2. Add configs to projects that need them:
     python add_deploy_config.py <project-name>

  3. Sync from GitHub:
     cd D:/Users/CASE/projects/<project>
     git pull

  4. Push local changes:
     cd D:/Users/CASE/projects/<project>
     git add .
     git commit -m "changes"
     git push
""")

print("=" * 70)
