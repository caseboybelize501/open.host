"""
Open.Host Jarvis - Enhanced GitHub Scanner (Non-Interactive)
============================================================
Scans and selects repos for deployment via command-line args
"""
import os
import sys
import requests
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Parse command line args
SELECTED_NUMBERS = []
if len(sys.argv) > 1:
    try:
        SELECTED_NUMBERS = [int(x) for x in sys.argv[1].split(',')]
    except:
        pass

print("=" * 70)
print("OPEN.HOST JARVIS - ENHANCED GITHUB SCANNER")
print("=" * 70)

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
USERNAME = os.getenv('GITHUB_USERNAME', 'caseboybelize501')

headers = {}
if GITHUB_TOKEN:
    headers['Authorization'] = f'token {GITHUB_TOKEN}'

print(f"\nUsername: {USERNAME}")
print(f"Token: {'[CONFIGURED]' if GITHUB_TOKEN else '[MISSING]'}")
if SELECTED_NUMBERS:
    print(f"Selection: {SELECTED_NUMBERS}")

print(f"\nFetching repositories...")
url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"

try:
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        print(f"[ERR] API error: {response.status_code}")
        exit(1)
    
    repos = response.json()
    print(f"[OK] Found {len(repos)} repositories")
    
    # Enhanced analysis
    print("\nAnalyzing repositories with deployment criteria...")
    
    for repo in repos:
        score = 0.0
        criteria_met = []
        
        if repo.get('fork') or repo.get('archived'):
            repo['profit_score'] = 0
            continue
        
        # Stars
        stars = repo.get('stargazers_count', 0)
        if stars > 100: score += 2.0; criteria_met.append('stars>100')
        elif stars > 10: score += 1.0; criteria_met.append('stars>10')
        elif stars > 0: score += 0.5; criteria_met.append('has stars')
        
        # Recent activity
        updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
        days_old = (datetime.now(updated.tzinfo) - updated).days
        repo['days_since_update'] = days_old
        if days_old < 7: score += 2.5; criteria_met.append('recent<7d')
        elif days_old < 30: score += 2.0; criteria_met.append('recent<30d')
        elif days_old < 90: score += 1.0; criteria_met.append('recent<90d')
        
        # README
        readme_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/readme"
        if requests.get(readme_url, headers=headers, timeout=5).status_code == 200:
            score += 1.5; criteria_met.append('README')
        
        # Deployable files
        contents_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/contents"
        contents_resp = requests.get(contents_url, headers=headers, timeout=5)
        if contents_resp.status_code == 200:
            contents = contents_resp.json()
            files = [f['name'] for f in contents] if isinstance(contents, list) else []
            
            for df in ['package.json', 'requirements.txt', 'setup.py', 'Cargo.toml']:
                if df in files:
                    score += 1.5; criteria_met.append(df)
                    break
            
            if 'package.json' in files and 'requirements.txt' in files:
                score += 1.0; criteria_met.append('fullstack')
        
        if repo.get('has_pages'): score += 1.0; criteria_met.append('pages')
        if repo.get('homepage'): score += 0.5; criteria_met.append('homepage')
        if repo.get('description'): score += 0.5; criteria_met.append('desc')
        if repo.get('size', 0) > 500: score += 1.0; criteria_met.append('size>500KB')
        elif repo.get('size', 0) > 100: score += 0.5; criteria_met.append('size>100KB')
        
        language = repo.get('language', '')
        if language in ['TypeScript', 'JavaScript', 'Python', 'Rust', 'Go']:
            score += 0.5; criteria_met.append(language)
        
        if repo.get('has_issues'): score += 0.3; criteria_met.append('issues')
        if repo.get('has_wiki'): score += 0.3; criteria_met.append('wiki')
        
        topics = repo.get('topics', [])
        if topics: score += min(len(topics) * 0.2, 0.6); criteria_met.append(f'{len(topics)} topics')
        
        repo['profit_score'] = min(score, 10.0)
        repo['criteria_met'] = criteria_met
    
    # Sort
    all_repos_sorted = sorted(repos, key=lambda x: x.get('profit_score', 0), reverse=True)
    profitable = [r for r in all_repos_sorted if r.get('profit_score', 0) >= 5.0]
    
    print(f"\nResults:")
    print(f"  Total: {len(repos)} | Active: {len([r for r in repos if not r.get('fork') and not r.get('archived')])}")
    print(f"  Profitable (>=5.0): {len(profitable)}")
    
    # Show top 10
    print("\n" + "=" * 70)
    print("TOP 10 REPOSITORIES")
    print("=" * 70)
    
    for i, repo in enumerate(all_repos_sorted[:10], 1):
        marker = "[PROFITABLE]" if repo.get('profit_score', 0) >= 5.0 else ""
        print(f"{i:2}. {repo['name'][:30]:30} {marker}")
        print(f"    Score: {repo.get('profit_score', 0):4.1f} | {repo.get('language', 'Unknown'):12} | {repo.get('days_since_update', 0):3}d | {', '.join(repo.get('criteria_met', [])[:4])}")
    
    # Process selection
    selected_repos = []
    
    if SELECTED_NUMBERS:
        selected_repos = [all_repos_sorted[i-1] for i in SELECTED_NUMBERS if 0 < i <= len(all_repos_sorted)]
    else:
        # Auto-select top 5 profitable
        selected_repos = [r for r in all_repos_sorted if r.get('profit_score', 0) >= 5.0][:5]
    
    if selected_repos:
        print("\n" + "=" * 70)
        print("SELECTED FOR DEPLOYMENT")
        print("=" * 70)
        
        for i, repo in enumerate(selected_repos, 1):
            print(f"\n{i}. {repo['name']}")
            print(f"   Score: {repo.get('profit_score', 0):.1f}/10")
            print(f"   URL: {repo['html_url']}")
            print(f"   Language: {repo.get('language', 'Unknown')}")
            print(f"   Updated: {repo.get('days_since_update', 0)} days ago")
            print(f"   Criteria: {', '.join(repo.get('criteria_met', []))}")
            
            # Detect project type
            contents_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/contents"
            contents_resp = requests.get(contents_url, headers=headers, timeout=5)
            if contents_resp.status_code == 200:
                contents = contents_resp.json()
                files = [f['name'] for f in contents] if isinstance(contents, list) else []
                
                project_type = []
                if 'package.json' in files:
                    if any('next' in f.lower() for f in files): project_type.append('Next.js')
                    elif any('vite' in f.lower() for f in files): project_type.append('Vite')
                    elif any('react' in f.lower() for f in files): project_type.append('React')
                    else: project_type.append('Node.js')
                if 'requirements.txt' in files: project_type.append('Python')
                if 'index.html' in files: project_type.append('Static')
                if 'Cargo.toml' in files: project_type.append('Rust')
                
                if project_type:
                    print(f"   Type: {', '.join(project_type)}")
                
                # Recommend platform
                if 'Next.js' in project_type or 'React' in project_type:
                    print(f"   Recommended: Vercel")
                elif 'Python' in project_type:
                    print(f"   Recommended: Render")
                elif 'Static' in project_type:
                    print(f"   Recommended: Netlify or GitHub Pages")
        
        print("\n" + "=" * 70)
        print("READY FOR DEPLOYMENT")
        print("=" * 70)
        print(f"\nSelected {len(selected_repos)} repositories")
        print("\nTo deploy:")
        print("  1. Manual: Visit repo URLs and deploy via platform UI")
        print("  2. CLI: Use gh, vercel, or netlify commands")
        print("  3. Full workflow: Run with LLM when ready")
        
        # Save selection
        with open('selected_repos.txt', 'w') as f:
            f.write("SELECTED REPOSITORIES FOR DEPLOYMENT\n")
            f.write("=" * 50 + "\n\n")
            for repo in selected_repos:
                f.write(f"{repo['name']}\n")
                f.write(f"  URL: {repo['html_url']}\n")
                f.write(f"  Score: {repo.get('profit_score', 0):.1f}\n")
                f.write(f"  Language: {repo.get('language', 'Unknown')}\n")
                f.write(f"  Type: Detected\n\n")
        
        print(f"\n[OK] Selection saved to: selected_repos.txt")
        
except Exception as e:
    print(f"[ERR] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
