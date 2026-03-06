"""
Direct GitHub Scanner - No LLM
==============================
Simple GitHub API scanner without LLM dependencies
"""
import os
import requests
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("OPEN.HOST JARVIS - DIRECT GITHUB SCANNER")
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
    
    # Analyze
    print("\nAnalyzing repositories...")
    profitable = []
    
    for repo in repos:
        # Skip forks and archived
        if repo.get('fork') or repo.get('archived'):
            continue
        
        # Calculate score
        score = 0.0
        
        # Stars
        stars = repo.get('stargazers_count', 0)
        if stars > 100:
            score += 2.0
        elif stars > 10:
            score += 1.0
        
        # Recent activity
        updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
        days_old = (datetime.now(updated.tzinfo) - updated).days
        if days_old < 30:
            score += 2.0
        elif days_old < 90:
            score += 1.0
        
        # Has content
        if repo.get('has_wiki') or repo.get('description'):
            score += 1.0
        
        # Size
        if repo.get('size', 0) > 100:
            score += 1.0
        
        # Language
        if repo.get('language'):
            score += 0.5
        
        score = min(score, 10.0)
        repo['profit_score'] = score
        
        if score >= 5.0:
            profitable.append({
                'name': repo['name'],
                'score': score,
                'stars': stars,
                'language': repo.get('language', 'Unknown'),
                'updated_days_ago': days_old,
                'url': repo['html_url'],
                'description': repo.get('description', '')
            })
    
    # Sort all repos by score
    all_repos_sorted = sorted(repos, key=lambda x: x.get('profit_score', 0), reverse=True)
    
    # Sort by score
    profitable.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\nResults:")
    print(f"  Total repos: {len(repos)}")
    print(f"  Active (not fork/archived): {len([r for r in repos if not r.get('fork') and not r.get('archived')])}")
    print(f"  Profitable (score >= 5.0): {len(profitable)}")
    
    # Show top repos even if not profitable
    print("\n" + "=" * 70)
    print("TOP REPOSITORIES (by score)")
    print("=" * 70)
    
    for i, repo in enumerate(all_repos_sorted[:15], 1):
        print(f"\n{i}. {repo['name']} (Score: {repo.get('profit_score', 0):.1f})")
        print(f"   Stars: {repo.get('stargazers_count', 0)} | Language: {repo.get('language', 'Unknown')}")
        updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
        days_old = (datetime.now(updated.tzinfo) - updated).days
        print(f"   Updated: {days_old} days ago")
        print(f"   URL: {repo['html_url']}")
        if repo.get('description'):
            print(f"   Description: {repo['description'][:80]}")
    
    if profitable:
        print("\n" + "=" * 70)
        print("PROFITABLE REPOSITORIES (score >= 5.0)")
        print("=" * 70)
        
        for i, repo in enumerate(profitable[:20], 1):
            print(f"\n{i}. {repo['name']}")
            print(f"   Score: {repo['score']:.1f}/10")
            print(f"   Stars: {repo['stars']} | Language: {repo['language']}")
            print(f"   Updated: {repo['updated_days_ago']} days ago")
            print(f"   URL: {repo['url']}")
            if repo['description']:
                print(f"   Description: {repo['description']}")
    else:
        print("\n[INFO] No profitable repos found (score >= 5.0)")
        
except requests.Timeout:
    print("[ERR] Request timed out")
except Exception as e:
    print(f"[ERR] Failed: {e}")

print("\n" + "=" * 70)
