"""
Render.com API Automation
==========================
Automates deployment of Blueprint projects to Render.

Setup:
1. Get API Key: https://dashboard.render.com/u/settings/api
2. Set RENDER_API_KEY environment variable
3. Run: python deploy_to_render.py

API Docs: https://api-docs.render.com
"""
import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================
RENDER_API_KEY = os.getenv('RENDER_API_KEY', '')
RENDER_API_BASE = 'https://api.render.com/v1'

# Projects to deploy (caseboybelize501 GitHub repos)
TIER1_PROJECTS = [
    {'repo': 'daw', 'name': 'daw', 'branch': 'master'},
    {'repo': 'dev.portfolio', 'name': 'dev-portfolio', 'branch': 'master'},
    {'repo': 'fpga.design', 'name': 'fpga-design', 'branch': 'master'},
    {'repo': 'git.initv3', 'name': 'git-initv3', 'branch': 'master'},
    {'repo': 'git.intelli', 'name': 'git-intelli', 'branch': 'master'},
    {'repo': 'gpt.code.debug', 'name': 'gpt-code-debug', 'branch': 'master'},
    {'repo': 'legal', 'name': 'legal', 'branch': 'master'},
    {'repo': 'ml.learn', 'name': 'ml-learn', 'branch': 'master'},
    {'repo': 'RAM', 'name': 'ram', 'branch': 'master'},
    {'repo': 'tech.debt.code', 'name': 'tech-debt-code', 'branch': 'master'},
]

# ============================================================================
# RENDER API CLIENT
# ============================================================================
class RenderAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def list_services(self):
        """List all services"""
        resp = requests.get(f'{RENDER_API_BASE}/services', headers=self.headers)
        resp.raise_for_status()
        return resp.json()
    
    def create_service_from_blueprint(self, repo_url, branch, blueprint_path, service_name, plan='free'):
        """
        Create a new service from a Blueprint (render.yaml)
        
        API: POST /blueprints/deploy
        """
        payload = {
            'repository': {
                'url': repo_url,
                'branch': branch
            },
            'blueprintPath': blueprint_path,
            'service': {
                'name': service_name,
                'plan': plan
            }
        }
        
        resp = requests.post(
            f'{RENDER_API_BASE}/blueprints/deploy',
            headers=self.headers,
            json=payload
        )
        resp.raise_for_status()
        return resp.json()
    
    def deploy_service(self, service_id):
        """Trigger manual deploy for existing service"""
        payload = {'serviceId': service_id}
        resp = requests.post(
            f'{RENDER_API_BASE}/deploys',
            headers=self.headers,
            json=payload
        )
        resp.raise_for_status()
        return resp.json()
    
    def get_deploy_status(self, deploy_id):
        """Check deploy status"""
        resp = requests.get(
            f'{RENDER_API_BASE}/deploys/{deploy_id}',
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.json()
    
    def delete_service(self, service_id):
        """Delete a service"""
        resp = requests.delete(
            f'{RENDER_API_BASE}/services/{service_id}',
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.status_code == 204

# ============================================================================
# DEPLOYMENT WORKFLOW
# ============================================================================
def deploy_all_tier1(api_key, github_user='caseboybelize501'):
    """Deploy all Tier 1 projects"""
    if not api_key:
        print("ERROR: RENDER_API_KEY not set!")
        print("Get your API key at: https://dashboard.render.com/u/settings/api")
        print("\nSet it with:")
        print("  set RENDER_API_KEY=your_key_here")
        sys.exit(1)
    
    client = RenderAPI(api_key)
    
    print("=" * 70)
    print("RENDER AUTOMATED DEPLOYMENT - TIER 1")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"GitHub User: {github_user}")
    print()
    
    results = {'success': [], 'failed': [], 'skipped': []}
    
    for project in TIER1_PROJECTS:
        repo = project['repo']
        name = project['name']
        branch = project['branch']
        repo_url = f'https://github.com/{github_user}/{repo}'
        
        print(f"\n[{name}]")
        print(f"  Repo: {repo_url}")
        
        try:
            # Check if service already exists
            services = client.list_services()
            existing = [s for s in services if s['name'] == name]
            
            if existing:
                print(f"  [SKIP] Service already exists: {existing[0]['id']}")
                results['skipped'].append(f"{name}: Already deployed")
                
                # Trigger redeploy instead
                print(f"  [INFO] Triggering redeploy...")
                deploy = client.deploy_service(existing[0]['id'])
                print(f"  [OK] Deploy triggered: {deploy['id']}")
                results['success'].append(f"{name}: Redeployed")
                continue
            
            # Create new service from Blueprint
            print(f"  [INFO] Creating service from Blueprint...")
            result = client.create_service_from_blueprint(
                repo_url=repo_url,
                branch=branch,
                blueprint_path='render.yaml',
                service_name=name,
                plan='free'
            )
            
            service_id = result.get('service', {}).get('id', 'unknown')
            print(f"  [OK] Service created: {service_id}")
            print(f"  [URL] https://{name}.onrender.com")
            results['success'].append(f"{name}: {service_id}")
            
        except requests.exceptions.HTTPError as e:
            error_msg = str(e.response.text) if hasattr(e, 'response') else str(e)
            print(f"  [ERR] {error_msg}")
            results['failed'].append(f"{name}: {error_msg}")
        except Exception as e:
            print(f"  [ERR] {e}")
            results['failed'].append(f"{name}: {e}")
        
        # Rate limiting - wait between deploys
        time.sleep(2)
    
    # Summary
    print("\n" + "=" * 70)
    print("DEPLOYMENT SUMMARY")
    print("=" * 70)
    print(f"Success: {len(results['success'])}/{len(TIER1_PROJECTS)}")
    print(f"Failed:  {len(results['failed'])}/{len(TIER1_PROJECTS)}")
    print(f"Skipped: {len(results['skipped'])}/{len(TIER1_PROJECTS)}")
    
    if results['failed']:
        print("\nFailed deployments:")
        for item in results['failed']:
            print(f"  - {item}")
    
    if results['skipped']:
        print("\nSkipped (already deployed):")
        for item in results['skipped']:
            print(f"  - {item}")
    
    print(f"\nCompleted: {datetime.now().isoformat()}")
    return results

# ============================================================================
# CLI
# ============================================================================
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy to Render automatically')
    parser.add_argument('--api-key', help='Render API key (or set RENDER_API_KEY env var)')
    parser.add_argument('--user', default='caseboybelize501', help='GitHub username')
    parser.add_argument('--list', action='store_true', help='List existing services')
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.getenv('RENDER_API_KEY')
    
    if args.list:
        if not api_key:
            print("ERROR: RENDER_API_KEY required")
            sys.exit(1)
        client = RenderAPI(api_key)
        services = client.list_services()
        print(f"Found {len(services)} services:")
        for s in services:
            print(f"  - {s['name']} ({s['id']}) - {s['serviceDetails']['plan']}")
    else:
        deploy_all_tier1(api_key, args.user)
