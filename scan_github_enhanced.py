"""
Open.Host Jarvis - Enhanced GitHub Scanner
==========================================
With enhanced deployment criteria and manual selection
"""
import os
import requests
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("OPEN.HOST JARVIS - ENHANCED GITHUB SCANNER")
print("=" * 70)

# Get token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
USERNAME = os.getenv('GITHUB_USERNAME', 'caseboybelize501')

headers = {}
if GITHUB_TOKEN:
    headers['Authorization'] = f'token {GITHUB_TOKEN}'

print(f"\nUsername: {USERNAME}")
print(f"Token: {'[CONFIGURED]' if GITHUB_TOKEN else '[MISSING]'}")

# Fetch repos
print(f"\nFetching repositories...")
url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100"

try:
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 401:
        print("[ERR] Invalid GitHub token")
        exit(1)
    elif response.status_code == 404:
        print(f"[ERR] User '{USERNAME}' not found")
        exit(1)
    elif response.status_code != 200:
        print(f"[ERR] API error: {response.status_code}")
        exit(1)
    
    repos = response.json()
    print(f"[OK] Found {len(repos)} repositories")
    
    # Enhanced analysis with deployment criteria
    print("\nAnalyzing repositories with deployment criteria...")
    
    for repo in repos:
        score = 0.0
        criteria_met = []
        
        # Skip forks and archived
        if repo.get('fork') or repo.get('archived'):
            repo['profit_score'] = 0
            repo['skip_reason'] = 'fork or archived'
            continue
        
        # === ENHANCED DEPLOYMENT CRITERIA ===
        
        # 1. Stars (community validation)
        stars = repo.get('stargazers_count', 0)
        if stars > 100:
            score += 2.0
            criteria_met.append('stars>100')
        elif stars > 10:
            score += 1.0
            criteria_met.append('stars>10')
        elif stars > 0:
            score += 0.5
            criteria_met.append('has stars')
        
        # 2. Recent activity
        updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
        days_old = (datetime.now(updated.tzinfo) - updated).days
        if days_old < 7:
            score += 2.5
            criteria_met.append('very recent (<7d)')
        elif days_old < 30:
            score += 2.0
            criteria_met.append('recent (<30d)')
        elif days_old < 90:
            score += 1.0
            criteria_met.append('active (<90d)')
        
        # 3. Has README (documentation)
        readme_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/readme"
        readme_resp = requests.get(readme_url, headers=headers, timeout=5)
        has_readme = readme_resp.status_code == 200
        if has_readme:
            score += 1.5
            criteria_met.append('has README')
        
        # 4. Has package.json or requirements.txt (deployable)
        contents_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/contents"
        contents_resp = requests.get(contents_url, headers=headers, timeout=5)
        deployable_files = ['package.json', 'requirements.txt', 'setup.py', 'Cargo.toml', 'go.mod', 'pyproject.toml']
        
        if contents_resp.status_code == 200:
            contents = contents_resp.json()
            files = [f['name'] for f in contents] if isinstance(contents, list) else []
            
            found_deploy = False
            for df in deployable_files:
                if df in files:
                    score += 1.5
                    criteria_met.append(f'has {df}')
                    found_deploy = True
                    break
            
            # Bonus for having both frontend and backend
            if 'package.json' in files and 'requirements.txt' in files:
                score += 1.0
                criteria_met.append('fullstack')
        
        # 5. Has GitHub Pages enabled
        if repo.get('has_pages'):
            score += 1.0
            criteria_met.append('pages enabled')
        
        # 6. Has website in description
        if repo.get('homepage'):
            score += 0.5
            criteria_met.append('has homepage')
        
        # 7. Has description
        if repo.get('description'):
            score += 0.5
            criteria_met.append('has description')
        
        # 8. Size (non-empty project)
        if repo.get('size', 0) > 500:  # >500KB
            score += 1.0
            criteria_met.append('substantial size')
        elif repo.get('size', 0) > 100:
            score += 0.5
            criteria_met.append('has content')
        
        # 9. Language (popular deployable languages)
        language = repo.get('language', '')
        deploy_languages = ['TypeScript', 'JavaScript', 'Python', 'Rust', 'Go', 'Ruby', 'PHP']
        if language in deploy_languages:
            score += 0.5
            criteria_met.append(f'{language}')
        
        # 10. Has issues enabled (active maintenance)
        if repo.get('has_issues'):
            score += 0.3
            criteria_met.append('issues enabled')
        
        # 11. Has wiki (documentation)
        if repo.get('has_wiki'):
            score += 0.3
            criteria_met.append('wiki enabled')
        
        # 12. Topics (categorization)
        topics = repo.get('topics', [])
        if topics:
            score += min(len(topics) * 0.2, 0.6)
            criteria_met.append(f'{len(topics)} topics')
        
        score = min(score, 10.0)
        repo['profit_score'] = score
        repo['criteria_met'] = criteria_met
        repo['days_since_update'] = days_old
    
    # Sort all repos by score
    all_repos_sorted = sorted(repos, key=lambda x: x.get('profit_score', 0), reverse=True)
    
    # Filter profitable
    profitable = [r for r in all_repos_sorted if r.get('profit_score', 0) >= 5.0]
    
    print(f"\nResults:")
    print(f"  Total repos: {len(repos)}")
    print(f"  Active (not fork/archived): {len([r for r in repos if not r.get('fork') and not r.get('archived')])}")
    print(f"  Profitable (score >= 5.0): {len(profitable)}")
    
    # Display top repos with criteria
    print("\n" + "=" * 70)
    print("TOP REPOSITORIES (by deployment readiness score)")
    print("=" * 70)
    
    for i, repo in enumerate(all_repos_sorted[:15], 1):
        score = repo.get('profit_score', 0)
        marker = "[PROFITABLE]" if score >= 5.0 else ""
        
        print(f"\n{i}. {repo['name']} {marker}")
        print(f"   Score: {score:.1f}/10 | Stars: {repo.get('stargazers_count', 0)}")
        print(f"   Language: {repo.get('language', 'Unknown')} | Updated: {repo.get('days_since_update', 0)} days ago")
        
        criteria = repo.get('criteria_met', [])
        if criteria:
            print(f"   Criteria: {', '.join(criteria)}")
        
        print(f"   URL: {repo['html_url']}")
        if repo.get('description'):
            desc = repo['description'][:80]
            print(f"   Description: {desc}")
    
    # Manual selection
    print("\n" + "=" * 70)
    print("MANUAL SELECTION")
    print("=" * 70)
    print("\nEnter repo numbers to select for deployment (comma-separated, e.g., 1,3,5):")
    print("Or press Enter to skip selection")
    
    try:
        selection = input("> ").strip()
        if selection:
            selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_repos = [all_repos_sorted[i] for i in selected_indices if 0 <= i < len(all_repos_sorted)]
            
            if selected_repos:
                print("\n" + "=" * 70)
                print("SELECTED REPOSITORIES FOR DEPLOYMENT")
                print("=" * 70)
                
                for i, repo in enumerate(selected_repos, 1):
                    print(f"\n{i}. {repo['name']}")
                    print(f"   Score: {repo.get('profit_score', 0):.1f}")
                    print(f"   URL: {repo['html_url']}")
                    print(f"   Language: {repo.get('language', 'Unknown')}")
                    
                    # Show deployment hints
                    contents_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/contents"
                    contents_resp = requests.get(contents_url, headers=headers, timeout=5)
                    if contents_resp.status_code == 200:
                        contents = contents_resp.json()
                        files = [f['name'] for f in contents] if isinstance(contents, list) else []
                        
                        deploy_hints = []
                        if 'package.json' in files:
                            deploy_hints.append('Node.js project')
                            if 'next.config' in str(files):
                                deploy_hints.append('Next.js')
                            elif 'vite.config' in str(files):
                                deploy_hints.append('Vite')
                            elif 'react' in str(files).lower():
                                deploy_hints.append('React')
                        
                        if 'requirements.txt' in files:
                            deploy_hints.append('Python project')
                        
                        if 'index.html' in files:
                            deploy_hints.append('Static site')
                        
                        if deploy_hints:
                            print(f"   Type: {', '.join(deploy_hints)}")
                
                print("\n[OK] Repositories selected! Ready for deployment.")
                print("\nNext steps:")
                print("  1. Run: python deploy_selected.py")
                print("  2. Or deploy manually via GitHub Pages/Netlify/Vercel")
            else:
                print("\n[INFO] No valid repos selected")
        else:
            print("\n[INFO] No manual selection made")
    except Exception as e:
        print(f"\n[INFO] Selection skipped: {e}")
        
except requests.Timeout:
    print("[ERR] Request timed out")
except Exception as e:
    print(f"[ERR] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
