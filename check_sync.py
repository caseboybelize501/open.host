"""
Check case sensitivity issues between GitHub and local
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

# Fetch GitHub repos
url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100"
response = requests.get(url, headers=headers, timeout=30)
github_repos = {r['name'].lower(): r['name'] for r in response.json()}

# Get local (lowercase for comparison)
local_projects = {}
for proj_dir in LOCAL_PROJECTS.iterdir():
    if proj_dir.is_dir() and not proj_dir.name.startswith('.') and not proj_dir.name.startswith('_'):
        local_projects[proj_dir.name.lower()] = proj_dir.name

print("=" * 70)
print("CASE SENSITIVITY ANALYSIS")
print("=" * 70)

# Find matches (case-insensitive)
matched = set(github_repos.keys()) & set(local_projects.keys())
github_only = set(github_repos.keys()) - set(local_projects.keys())
local_only = set(local_projects.keys()) - set(github_repos.keys())

print(f"\nGitHub repos: {len(github_repos)}")
print(f"Local projects: {len(local_projects)}")
print(f"Matched (case-insensitive): {len(matched)}")

# Check case differences
print("\n" + "=" * 70)
print("CASE DIFFERENCES (GitHub vs Local)")
print("=" * 70)

case_diffs = []
for key in matched:
    github_name = github_repos[key]
    local_name = local_projects[key]
    if github_name != local_name:
        case_diffs.append((github_name, local_name))
        print(f"\n{github_name} <- GitHub")
        print(f"{local_name} <- Local")

print(f"\nTotal case differences: {len(case_diffs)}")

# True missing
print("\n" + "=" * 70)
print("TRUE MISSING (not just case)")
print("=" * 70)

print("\nOn GitHub but NOT local (true missing):")
for key in sorted(github_only):
    print(f"  - {github_repos[key]}")

print("\nLocal but NOT on GitHub:")
for key in sorted(local_only):
    print(f"  - {local_projects[key]}")

print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)

if case_diffs:
    print(f"""
{len(case_diffs)} projects have CASE DIFFERENCES.

On Windows, this doesn't matter for running locally.
But for Git operations, you should match GitHub's casing.

To fix, rename local folders to match GitHub:
""")
    for github_name, local_name in case_diffs[:10]:
        print(f"  ren {local_name} {github_name}")
    if len(case_diffs) > 10:
        print(f"  ... and {len(case_diffs) - 10} more")

if github_only:
    print(f"\n{len(github_only)} repos are truly missing locally - need to clone")

if local_only:
    print(f"\n{len(local_only)} local projects not on GitHub - push them or ignore")

print("=" * 70)
