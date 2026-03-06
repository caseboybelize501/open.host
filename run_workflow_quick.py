"""
Open.Host Jarvis - Quick Workflow (Lightweight)
===============================================
Skips heavy LLM loading, focuses on GitHub scanning and job creation
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("OPEN.HOST JARVIS - QUICK WORKFLOW")
print("=" * 70)
print(f"Started: {datetime.now().isoformat()}")

# ============================================================================
# STEP 1: SYSTEM SCAN (REQUIRED)
# ============================================================================
print("\n" + "=" * 70)
print("STEP 1: SYSTEM SCAN")
print("=" * 70)

from src.bootstrap.system_scanner import scan_system
from src.bootstrap.system_profile import HostingSystemProfile

print("\n[1.1] Running system bootstrap...")
try:
    scan_system()
    print("  [OK] System bootstrap complete")
except Exception as e:
    print(f"  [ERR] System bootstrap failed: {e}")
    sys.exit(1)

print("\n[1.2] Scanning for GGUF models...")
from src.llm.model_pool import get_model_pool

pool = get_model_pool()
models = pool.scan_for_models()
print(f"  [OK] Models found: {len(models)}")
for m in models:
    print(f"       - {m.name} ({m.parameters}, {m.quantization})")

# ============================================================================
# STEP 2: INITIALIZE AGENTS (Lightweight - No LLM Loading)
# ============================================================================
print("\n" + "=" * 70)
print("STEP 2: INITIALIZE AGENTS")
print("=" * 70)

print("\n[2.1] Initializing agents (lightweight mode)...")
try:
    from src.agents.master_agent import get_master_agent
    from src.agents.analyzer_agent import get_analyzer_agent
    from src.agents.memory_agent import get_memory_agent
    
    master = get_master_agent()
    analyzer = get_analyzer_agent()
    memory = get_memory_agent()
    
    # Wire up agents
    master.set_agents(analyzer=analyzer, deploy=None, memory=memory)
    
    print("  [OK] Master Agent: Ready")
    print("  [OK] Analyzer Agent: Ready")
    print("  [OK] Memory Agent: Ready")
except Exception as e:
    print(f"  [ERR] Agent init failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 3: GITHUB SCAN
# ============================================================================
print("\n" + "=" * 70)
print("STEP 3: GITHUB SCAN")
print("=" * 70)

github_username = os.getenv('GITHUB_USERNAME', 'caseboybelize501')
print(f"\n[3.1] Configuration")
print(f"  Username: {github_username}")
print(f"  Token: {'Configured' if os.getenv('GITHUB_TOKEN') else 'Missing'}")

print(f"\n[3.2] Scanning {github_username}'s repositories...")
try:
    in_progress = [
        job.repo_name for job in master.jobs.values()
        if job.status in ["pending", "analyzing", "deploying"]
    ]
    
    result = master.scan_and_create_jobs(
        github_username=github_username,
        in_progress_registry=in_progress
    )
    
    scan_result = result.get('scan_result', {})
    
    print(f"\n  [OK] Scan complete")
    print(f"       Total repos: {scan_result.get('total_repos', 0)}")
    print(f"       Active repos: {scan_result.get('active_repos', 0)}")
    print(f"       Profitable repos: {result.get('total_profitable', 0)}")
    print(f"       Jobs created: {result.get('created_jobs', 0)}")
    print(f"       Queue length: {len(master.job_queue)}")
    
    # Show created jobs
    if master.jobs:
        print(f"\n  Jobs created:")
        for job_id, job in list(master.jobs.items())[:10]:
            print(f"    - {job.repo_name}")
            print(f"      Score: {job.profit_score} | Status: {job.status}")
            print(f"      URL: {job.repo_url}")
    
except Exception as e:
    print(f"  [ERR] GitHub scan failed: {e}")
    print(f"  Note: Check GITHUB_TOKEN is valid")
    import traceback
    traceback.print_exc()

# ============================================================================
# STEP 4: MEMORY SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("STEP 4: MEMORY SYSTEM")
print("=" * 70)

try:
    memory_summary = memory.get_memory_summary()
    print(f"\n  [OK] Memory Summary:")
    print(f"       Total failures tracked: {memory_summary.get('total_failures', 0)}")
    print(f"       Total strategies: {memory_summary.get('total_strategies', 0)}")
    print(f"       Total patterns: {memory_summary.get('total_patterns', 0)}")
    
    drift_summary = memory.get_drift_summary()
    print(f"\n  [OK] Drift Tracking:")
    print(f"       Total drift events: {len(drift_summary.get('drift_events', []))}")
    
except Exception as e:
    print(f"  [ERR] Memory query failed: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("WORKFLOW COMPLETE")
print("=" * 70)

print(f"\nSystem Status:")
print(f"  Models Available: {len(models)}")
print(f"  Agents Ready: 3/3")
print(f"  Jobs Created: {len(master.jobs)}")
print(f"  Jobs Pending: {len(master.job_queue)}")
print(f"  Jobs Completed: {len(master.completed_jobs)}")

if master.job_queue:
    print(f"\nNext Steps:")
    print(f"  - Jobs are queued and ready for processing")
    print(f"  - To process: Run full workflow with LLM enabled")
    print(f"  - Or call: master.process_job_queue()")

print(f"\nCompleted: {datetime.now().isoformat()}")
print("=" * 70)
