"""
Complete Analysis of ALL 72 GitHub Repos
"""
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_USER = 'caseboybelize501'
LOCAL_PROJECTS = Path(r"D:/Users/CASE/projects")

print("=" * 70)
print("COMPLETE REPO ANALYSIS - ALL 72 PROJECTS")
print("=" * 70)

# Scan all projects
projects = []

for proj_dir in LOCAL_PROJECTS.iterdir():
    if not proj_dir.is_dir():
        continue
    if proj_dir.name.startswith('.') or proj_dir.name.startswith('_'):
        continue
    
    # Check ALL deployment indicators
    has_dockerfile = (proj_dir / 'Dockerfile').exists()
    has_render_yaml = (proj_dir / 'render.yaml').exists()
    has_package_json = (proj_dir / 'package.json').exists()
    has_requirements = (proj_dir / 'requirements.txt').exists()
    has_setup_py = (proj_dir / 'setup.py').exists()
    has_pyproject = (proj_dir / 'pyproject.toml').exists()
    has_cargo = (proj_dir / 'Cargo.toml').exists()
    has_go_mod = (proj_dir / 'go.mod').exists()
    has_index_html = (proj_dir / 'index.html').exists()
    has_readme = (proj_dir / 'README.md').exists()
    has_git = (proj_dir / '.git').exists()
    
    # Check for framework configs
    has_nextjs = (proj_dir / 'next.config.js').exists() or (proj_dir / 'next.config.ts').exists()
    has_vite = (proj_dir / 'vite.config.js').exists() or (proj_dir / 'vite.config.ts').exists()
    has_react = any('react' in f.name.lower() for f in proj_dir.glob('*.config.*'))
    has_vue = (proj_dir / 'vue.config.js').exists()
    has_nuxt = (proj_dir / 'nuxt.config.js').exists()
    has_svelte = (proj_dir / 'svelte.config.js').exists()
    
    # Check docker-compose
    has_docker_compose = (proj_dir / 'docker-compose.yml').exists() or (proj_dir / 'docker-compose.yaml').exists()
    
    # Check Procfile (Heroku/Render)
    has_procfile = (proj_dir / 'Procfile').exists()
    
    # Determine project type
    project_types = []
    if has_package_json:
        if has_nextjs: project_types.append('Next.js')
        elif has_vite: project_types.append('Vite')
        elif has_vue: project_types.append('Vue')
        elif has_nuxt: project_types.append('Nuxt')
        elif has_svelte: project_types.append('Svelte')
        elif has_react: project_types.append('React')
        else: project_types.append('Node.js')
    if has_requirements or has_setup_py or has_pyproject: project_types.append('Python')
    if has_cargo: project_types.append('Rust')
    if has_go_mod: project_types.append('Go')
    if has_index_html and not has_package_json: project_types.append('Static')
    
    # Calculate deployment readiness
    deploy_score = 0
    deploy_indicators = []
    
    if has_dockerfile: deploy_score += 5; deploy_indicators.append('Dockerfile')
    if has_render_yaml: deploy_score += 5; deploy_indicators.append('render.yaml')
    if has_procfile: deploy_score += 3; deploy_indicators.append('Procfile')
    if has_docker_compose: deploy_score += 2; deploy_indicators.append('docker-compose')
    if has_package_json: deploy_score += 1; deploy_indicators.append('package.json')
    if has_requirements: deploy_score += 1; deploy_indicators.append('requirements.txt')
    if has_cargo: deploy_score += 1; deploy_indicators.append('Cargo.toml')
    if has_go_mod: deploy_score += 1; deploy_indicators.append('go.mod')
    if has_index_html: deploy_score += 1; deploy_indicators.append('index.html')
    if has_readme: deploy_score += 0.5; deploy_indicators.append('README.md')
    
    # Determine deployment platforms
    platforms = []
    if has_dockerfile or has_docker_compose:
        platforms.extend(['Render', 'Fly.io', 'Railway', 'Google Cloud Run'])
    if has_render_yaml:
        platforms.append('Render (configured)')
    if has_procfile:
        platforms.extend(['Render', 'Heroku'])
    if 'Next.js' in project_types or 'React' in project_types:
        platforms.append('Vercel')
    if has_index_html and not project_types:
        platforms.extend(['Netlify', 'Vercel', 'GitHub Pages'])
    if 'Python' in project_types:
        platforms.extend(['Render', 'Railway'])
    if 'Rust' in project_types:
        platforms.append('Render')
    if 'Go' in project_types:
        platforms.extend(['Render', 'Fly.io', 'Railway'])
    
    platforms = list(set(platforms))
    
    projects.append({
        'name': proj_dir.name,
        'path': proj_dir,
        'types': project_types,
        'deploy_score': deploy_score,
        'indicators': deploy_indicators,
        'platforms': platforms,
        'has_dockerfile': has_dockerfile,
        'has_render_yaml': has_render_yaml,
        'has_package_json': has_package_json,
        'has_requirements': has_requirements,
        'has_readme': has_readme,
        'has_git': has_git
    })

# Sort by deployment score
projects.sort(key=lambda x: x['deploy_score'], reverse=True)

print(f"\nTotal Projects Analyzed: {len(projects)}")

# Show ALL projects
print("\n" + "=" * 70)
print("ALL PROJECTS - DEPLOYMENT READINESS")
print("=" * 70)

for i, proj in enumerate(projects, 1):
    score = proj['deploy_score']
    ready = "READY" if score >= 5 else "NEEDS WORK" if score >= 2 else "MINIMAL"
    
    print(f"\n{i:2}. {proj['name'][:40]:40} Score: {score:4.1f} [{ready}]")
    print(f"    Type: {', '.join(proj['types']) if proj['types'] else 'Unknown'}")
    print(f"    Files: {', '.join(proj['indicators'][:5])}")
    if proj['platforms']:
        print(f"    Deploy: {', '.join(proj['platforms'][:3])}")

# Summary by readiness
print("\n" + "=" * 70)
print("SUMMARY BY DEPLOYMENT READINESS")
print("=" * 70)

ready = [p for p in projects if p['deploy_score'] >= 5]
needs_work = [p for p in projects if 2 <= p['deploy_score'] < 5]
minimal = [p for p in projects if p['deploy_score'] < 2]

print(f"""
DEPLOYMENT READY (score >= 5): {len(ready)}
  These have Dockerfile, render.yaml, or strong indicators

NEEDS CONFIG (score 2-4): {len(needs_work)}
  These have package.json/requirements but no deploy config

MINIMAL (score < 2): {len(minimal)}
  Basic projects, need deployment setup
""")

# Show what's needed for minimal projects
if minimal:
    print("\n" + "=" * 70)
    print("MINIMAL PROJECTS - WHAT THEY NEED")
    print("=" * 70)
    
    for proj in minimal[:15]:
        needs = []
        if not proj['has_readme']: needs.append('README.md')
        if not proj['has_package_json'] and not proj['has_requirements']:
            needs.append('package.json or requirements.txt')
        if not proj['has_dockerfile'] and not proj['has_render_yaml']:
            needs.append('Dockerfile or render.yaml')
        
        print(f"  {proj['name']}: {', '.join(needs)}")

# Show top deployment candidates
print("\n" + "=" * 70)
print("TOP 20 DEPLOYMENT CANDIDATES")
print("=" * 70)

for i, proj in enumerate(projects[:20], 1):
    print(f"\n{i}. {proj['name']}")
    print(f"   Score: {proj['deploy_score']:.1f}/10")
    print(f"   Type: {', '.join(proj['types'])}")
    print(f"   Ready for: {', '.join(proj['platforms'][:4])}")

print("\n" + "=" * 70)
