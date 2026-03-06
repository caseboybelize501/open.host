"""
Open.Host Jarvis - GitHub Scanner Only
=======================================
Minimal workflow: Just scans GitHub and shows profitable repos
No LLM loading, no agents
"""
import os
import sys
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("OPEN.HOST JARVIS - GITHUB SCANNER")
print("=" * 70)
print(f"Started: {datetime.now().isoformat()}")

# ============================================================================
# STEP 1: SYSTEM SCAN (Minimal)
# ============================================================================
print("\n" + "=" * 70)
print("STEP 1: SYSTEM SCAN")
print("=" * 70)

from src.bootstrap.system_scanner import scan_system

print("\n[1.1] Running system bootstrap...")
try:
    scan_system()
    print("  [OK] System bootstrap complete")
except Exception as e:
    print(f"  [WARN] Bootstrap issue: {e}")

print("\n[1.2] GGUF Models...")
from src.llm.model_pool import get_model_pool
pool = get_model_pool()
models = pool.scan_for_models()
print(f"  [OK] Models available: {len(models)}")

# ============================================================================
# STEP 2: GITHUB SCAN (Direct)
# ============================================================================
print("\n" + "=" * 70)
print("STEP 2: GITHUB REPOSITORY SCAN")
print("=" * 70)

github_username = os.getenv('GITHUB_USERNAME', 'caseboybelize501')
print(f"\n[2.1] Configuration")
print(f"  Username: {github_username}")
print(f"  Token: {'[CONFIGURED]' if os.getenv('GITHUB_TOKEN') else '[MISSING]'}")

if not os.getenv('GITHUB_TOKEN'):
    print("\n  [!] GitHub token required for API access")
    print("      Token has been configured in .env file")
    print("      Proceeding with unauthenticated scan (limited to 60 req/hr)")

print(f"\n[2.2] Scanning repositories...")

repos = []
profitable_repos = []

try:
    from src.github.github_scanner import get_github_scanner
    
    scanner = get_github_scanner()
    
    # Scan repos
    repos = scanner.scan_repositories(github_username)
    
    print(f"\n  [OK] Found {len(repos)} repositories")
    
    # Filter and analyze
    print("\n[2.3] Analyzing repositories...")
    
    profitable_repos = []
    for repo in repos:
        # Skip forks and archived
        if repo.fork or repo.archived:
            continue
        
        # Calculate simple profit score
        score = 0.0
        
        # Stars
        if repo.stars > 100:
            score += 2.0
        elif repo.stars > 10:
            score += 1.0
        
        # Recent activity
        days_since_update = (datetime.now() - repo.updated_at).days
        if days_since_update < 30:
            score += 2.0
        elif days_since_update < 90:
            score += 1.0
        
        # Has README
        if repo.has_wiki or repo.description:
            score += 1.0
        
        # Not empty
        if repo.size > 0:
            score += 1.0
        
        # Language
        if repo.language:
            score += 0.5
        
        repo.profit_score = min(score, 10.0)
        
        if score >= 5.0:
            profitable_repos.append(repo)
    
    print(f"  [OK] Analysis complete")
    print(f"       Total repos: {len(repos)}")
    print(f"       Active (not fork/archived): {len([r for r in repos if not r.fork and not r.archived])}")
    print(f"       Profitable (score >= 5.0): {len(profitable_repos)}")
    
    # Display profitable repos
    if profitable_repos:
        print("\n" + "=" * 70)
        print("PROFITABLE REPOSITORIES")
        print("=" * 70)
        
        profitable_repos.sort(key=lambda x: x.profit_score, reverse=True)
        
        for i, repo in enumerate(profitable_repos[:20], 1):
            days_old = (datetime.now() - repo.updated_at).days
            print(f"\n{i}. {repo.name}")
            print(f"   Score: {repo.profit_score:.1f}/10")
            print(f"   Stars: {repo.stars} | Forks: {repo.forks_count}")
            print(f"   Language: {repo.language or 'Unknown'}")
            print(f"   Updated: {days_old} days ago")
            print(f"   URL: {repo.html_url}")
            if repo.description:
                print(f"   Description: {repo.description}")
    else:
        print("\n  [INFO] No profitable repos found (score >= 5.0)")
        print("         Repos may need more stars or recent activity")
    
except Exception as e:
    print(f"  [ERR] Scan failed: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("SCAN COMPLETE")
print("=" * 70)

print(f"\nResults:")
print(f"  Models Available: {len(models)}")
print(f"  Repositories Scanned: {len(repos) if 'repos' in locals() else 0}")
print(f"  Profitable Found: {len(profitable_repos) if 'profitable_repos' in locals() else 0}")

if profitable_repos:
    print(f"\nNext Steps:")
    print(f"  1. Review profitable repos above")
    print(f"  2. Run full workflow to deploy: python run_workflow.py")
    print(f"  3. Or deploy manually via GitHub Pages/Netlify/Vercel")

print(f"\nCompleted: {datetime.now().isoformat()}")
print("=" * 70)
