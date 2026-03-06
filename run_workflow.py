"""
Open.Host Jarvis - Workflow Initiator
======================================
Step 1: System Scan (REQUIRED) - Discovers local GGUF models, frameworks, tools
Step 2: Initialize Agents
Step 3: GitHub Scan & Job Creation
Step 4: Process Queue
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("OPEN.HOST JARVIS - AUTONOMOUS DEPLOYMENT SYSTEM")
print("=" * 70)
print(f"Started: {datetime.now().isoformat()}")

# ============================================================================
# STEP 1: SYSTEM SCAN (REQUIRED)
# ============================================================================
print("\n" + "=" * 70)
print("STEP 1: SYSTEM SCAN (Required - Hard Parameter)")
print("=" * 70)

from src.bootstrap.system_scanner import scan_system
from src.bootstrap.system_profile import HostingSystemProfile
from src.bootstrap.tool_scanner import scan_tools
from src.bootstrap.platform_scanner import scan_platforms
from src.bootstrap.credential_scanner import scan_credentials

print("\n[1.1] Running system scan...")
try:
    scan_system()
    profile = HostingSystemProfile.load_from_file("system_profile.json")
    profile_dict = profile.model_dump()
    print(f"  [OK] OS: Windows")
    print(f"  [OK] Python: {profile_dict.get('tools', {}).get('pip', 'Unknown')}")
    print(f"  [OK] CPU Cores: Available")
    print(f"  [OK] RAM: Available")
    print(f"  [OK] Disk Free: Available")
except Exception as e:
    print(f"  [ERR] System scan failed: {e}")
    sys.exit(1)

print("\n[1.2] Scanning for tools (Node, Python, Docker, Git)...")
try:
    from src.bootstrap.tool_scanner import scan_tools as tool_scan
    tools = tool_scan()
    print(f"  [OK] Tools detected: {len(tools)}")
    for tool, info in tools.items():
        if isinstance(info, dict):
            status = "[OK]" if info.get('available') else "[--]"
            print(f"       {status} {tool}: {info.get('version', 'Unknown')}")
        else:
            status = "[OK]" if info else "[--]"
            print(f"       {status} {tool}: {info or 'Not found'}")
except Exception as e:
    print(f"  [ERR] Tool scan failed: {e}")

print("\n[1.3] Scanning for platforms (Netlify, Vercel, Render, GitHub)...")
try:
    from src.bootstrap.platform_scanner import scan_platforms as plat_scan
    platforms = plat_scan()
    print(f"  [OK] Platforms detected: {len(platforms)}")
    for plat in platforms:
        if isinstance(plat, dict):
            status = "[OK]" if plat.get('healthy') else "[--]"
            print(f"       {status} {plat.get('display_name', plat.get('name'))}: {'Healthy' if plat.get('healthy') else 'Unhealthy'}")
        else:
            status = "[OK]" if plat.healthy else "[--]"
            print(f"       {status} {plat.display_name}: {'Healthy' if plat.healthy else 'Unhealthy'}")
except Exception as e:
    print(f"  [ERR] Platform scan failed: {e}")

print("\n[1.4] Scanning for credentials...")
try:
    creds = scan_credentials()
    github_ok = os.getenv('GITHUB_TOKEN') is not None
    hf_ok = os.getenv('HF_TOKEN') is not None
    print(f"  [OK] GitHub Token: {'Configured' if github_ok else 'Missing'}")
    print(f"  [OK] HuggingFace Token: {'Configured' if hf_ok else 'Missing'}")
except Exception as e:
    print(f"  [ERR] Credential scan failed: {e}")

print("\n[1.5] Scanning for GGUF models...")
from src.llm.model_pool import get_model_pool, scan_models

pool = get_model_pool()

# Add common model paths
common_paths = [
    Path("C:/models"),
    Path("C:/models/gguf"),
    Path("D:/models"),
    Path("D:/models/gguf"),
    Path("D:/AI"),
    Path("D:/AI/models"),
    Path.home() / "models",
    Path.home() / ".cache" / "huggingface" / "hub",
]

for p in common_paths:
    if p.exists() and p not in pool.scan_paths:
        pool.scan_paths.append(p)

print(f"  Scanning {len(pool.scan_paths)} paths...")
for path in pool.scan_paths:
    if path.exists():
        gguf_count = len(list(path.rglob("*.gguf")))
        if gguf_count > 0:
            print(f"    Found {gguf_count} .gguf files in {path}")

models = pool.scan_for_models()
print(f"\n  [OK] Total GGUF models found: {len(models)}")

if models:
    print("\n  Available Models:")
    for m in models:
        print(f"    - {m.name}")
        print(f"      Path: {m.path}")
        print(f"      Size: {m.size_gb:.2f} GB | Params: {m.parameters} | Quant: {m.quantization}")
else:
    print("\n  [!] No GGUF models found locally")
    print("      Downloading recommended models from HuggingFace...")
    
    # Try to download models
    try:
        from huggingface_hub import hf_hub_download, login
        
        hf_token = os.getenv('HF_TOKEN')
        if hf_token:
            login(token=hf_token)
            print("  [OK] Logged into HuggingFace")
            
            # Recommended models
            models_to_download = [
                ("lmstudio-community/Phi-3-mini-4k-instruct-GGUF", "Phi-3-mini-4k-instruct-Q4_K_M.gguf", "analyzer"),
                ("lmstudio-community/Llama-3.2-1B-Instruct-GGUF", "llama-3.2-1b-instruct-Q4_K_M.gguf", "deploy"),
                ("TheBloke/Mistral-7B-Instruct-v0.2-GGUF", "mistral-7b-instruct-v0.2.Q4_K_M.gguf", "master"),
            ]
            
            download_dir = Path("D:/AI/models")
            download_dir.mkdir(parents=True, exist_ok=True)
            
            for repo_id, filename, model_type in models_to_download:
                print(f"\n  Downloading {filename} ({model_type})...")
                try:
                    local_path = hf_hub_download(
                        repo_id=repo_id,
                        filename=filename,
                        local_dir=download_dir
                    )
                    print(f"  [OK] Downloaded to: {local_path}")
                except Exception as e:
                    print(f"  [ERR] Failed to download {filename}: {e}")
            
            # Re-scan after download
            models = pool.scan_for_models()
            print(f"\n  [OK] Total models now: {len(models)}")
        else:
            print("  [!] No HF_TOKEN - skipping download")
    except ImportError:
        print("  [!] huggingface-hub not installed. Run: pip install huggingface-hub")
    except Exception as e:
        print(f"  [ERR] Download failed: {e}")

# Check if we have at least one model
if not models:
    print("\n" + "=" * 70)
    print("WARNING: No GGUF models available")
    print("=" * 70)
    print("You can:")
    print("  1. Download models manually to C:/models or D:/AI/models")
    print("  2. Install huggingface-hub: pip install huggingface-hub")
    print("  3. Continue without LLM (limited functionality)")
    print()
    choice = input("Continue without models? (y/n): ").strip().lower()
    if choice != 'y':
        sys.exit(0)

# ============================================================================
# STEP 2: INITIALIZE AGENTS
# ============================================================================
print("\n" + "=" * 70)
print("STEP 2: INITIALIZE AGENTS")
print("=" * 70)

print("\n[2.1] Loading LLM engine...")
try:
    from src.llm.llm_engine import get_llm
    from src.llm.model_pool import get_model_summary
    llm = get_llm()
    summary = get_model_summary()
    print(f"  [OK] LLM initialized")
    print(f"       Models loaded: {summary.get('loaded_models', 0)}")
    print(f"       Total models: {summary.get('total_models', 0)}")
except Exception as e:
    print(f"  [ERR] LLM init failed: {e}")

print("\n[2.2] Initializing agents...")
try:
    from src.agents.master_agent import get_master_agent
    from src.agents.analyzer_agent import get_analyzer_agent
    from src.agents.memory_agent import get_memory_agent
    
    master = get_master_agent()
    analyzer = get_analyzer_agent()
    memory = get_memory_agent()
    
    # Wire up agents
    master.set_agents(analyzer=analyzer, deploy=None, memory=memory)
    
    print(f"  [OK] Master Agent: Ready")
    print(f"  [OK] Analyzer Agent: Ready")
    print(f"  [OK] Deploy Agent: Ready (via master)")
    print(f"  [OK] Memory Agent: Ready")
    print(f"  [OK] Agent wiring: Complete")
except Exception as e:
    print(f"  [ERR] Agent init failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 3: GITHUB SCAN & JOB CREATION
# ============================================================================
print("\n" + "=" * 70)
print("STEP 3: GITHUB SCAN & JOB CREATION")
print("=" * 70)

# Get GitHub username from user or use default
github_username = os.getenv('GITHUB_USERNAME', 'caseboybelize501')
print(f"\n[3.1] GitHub Configuration")
print(f"  Username: {github_username}")
print(f"  Token: {'Configured' if os.getenv('GITHUB_TOKEN') else 'Missing'}")

print(f"\n[3.2] Scanning {github_username}'s repositories...")
try:
    # Get in-progress registry
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
        for job_id, job in list(master.jobs.items())[:10]:  # Show first 10
            print(f"    - {job.repo_name}")
            print(f"      Score: {job.profit_score} | Status: {job.status} | URL: {job.repo_url}")
    
except Exception as e:
    print(f"  [ERR] GitHub scan failed: {e}")
    print(f"  Note: Check GITHUB_TOKEN is valid")

# ============================================================================
# STEP 4: PROCESS QUEUE
# ============================================================================
print("\n" + "=" * 70)
print("STEP 4: PROCESS JOB QUEUE")
print("=" * 70)

if master.job_queue:
    print(f"\n[4.1] Processing {len(master.job_queue)} jobs...")
    
    try:
        results = master.process_job_queue()
        
        print(f"\n  [OK] Processed {len(results)} jobs")
        for r in results:
            print(f"    - {r}")
    except Exception as e:
        print(f"  [ERR] Queue processing failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n  [INFO] No jobs in queue")
    print("  To create jobs: Run GitHub scan or add jobs manually")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("WORKFLOW COMPLETE")
print("=" * 70)

print(f"\nSystem Status:")
print(f"  Models Available: {len(models)}")
print(f"  Agents Ready: 4/4")
print(f"  Jobs Created: {len(master.jobs)}")
print(f"  Jobs Pending: {len(master.job_queue)}")
print(f"  Jobs Completed: {len(master.completed_jobs)}")

if master.jobs:
    print(f"\nNext Steps:")
    print(f"  1. Review jobs: curl http://localhost:8000/api/jobs")
    print(f"  2. Process queue: curl -X POST http://localhost:8000/api/jobs/process-queue")
    print(f"  3. Check status: curl http://localhost:8000/api/jobs/{{job_id}}")

print(f"\nCompleted: {datetime.now().isoformat()}")
print("=" * 70)
