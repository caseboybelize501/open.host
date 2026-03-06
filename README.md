# Open.Host Jarvis

**Multi-Agent LLM Orchestration System for Autonomous GitHub Repository Deployment**

An offline-first, self-learning system that:
1. Scans GitHub repositories (e.g., github.com/caseboybelize501)
2. Analyzes repos using local GGUF models (llama.cpp)
3. Filters for "profitable" deployment candidates
4. Deploys to optimal hosting platforms
5. Learns from every deployment via 4-layer memory + drift tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MASTER AGENT (Large GGUF 7B+)                │
│  - Scans GitHub repos (github.com/caseboybelize501/repositories)│
│  - Compares against "in-progress" registry                       │
│  - Decides: NEW JOB or SKIP                                      │
│  - Only processes "profitable" marked repos                      │
└─────────────────────────────────────────────────────────────────┐
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ANALYZER AGENT │  │  DEPLOY AGENT   │  │  MEMORY AGENT   │
│  (Small 1-3B)   │  │  (Small 1-3B)   │  │  (Drift Manager)│
│  - Code review  │  │  - Build config │  │  - Track state  │
│  - Tech stack   │  │  - Platform sel │  │  - Profit score │
│  - Risk assess  │  │  - Execute      │  │  - Mark profitable│
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
              ┌───────────────▼───────────────┐
              │      LOCAL MODEL POOL         │
              │  C:/D:/ GGUF files (offline)  │
              │  - llama-3.2-1B (analyzer)    │
              │  - phi-3-mini (deploy)        │
              │  - mistral-7B (master)        │
              └───────────────────────────────┘
```

## Key Features

### Multi-Agent LLM System
| Agent | Model Size | Responsibility |
|-------|-----------|----------------|
| **Master Agent** | 7B+ | Complex reasoning, job orchestration, go/no-go decisions |
| **Analyzer Agent** | 1-3B | Code analysis, tech stack detection, risk assessment |
| **Deploy Agent** | 1-3B | Build configuration, platform selection, deployment execution |
| **Memory Agent** | N/A | 4-layer memory + drift tracking, profitability management |

### Profitability-First Workflow
- **No jobs by default** - Only "profitable" repos are processed
- **Profit scoring** - Each repo scored 0-10 based on stars, activity, tech stack
- **Drift tracking** - Monitors profitability changes over time
- **Memory-informed** - Historical success/failure affects future decisions

### 4-Layer Memory System
```
Layer 1: Deployment Failure Store (ChromaDB)
  → Stores failure patterns per project type + platform
  → Query: "what fails for React on Netlify?"

Layer 2: Project Pattern Graph (Neo4j)
  → Graph of project types → platform success relationships
  → Query: "which platforms work for Next.js?"

Layer 3: Build Strategy Library
  → Effective build configurations per project type + platform
  → Query: "what build command works for Vue on Vercel?"

Layer 4: Meta-Learning Index (sklearn)
  → Predicts cycles-to-stable based on historical data
  → Query: "how many cycles for this project type?"

+ Drift Tracking:
  → Profitability drift over time
  → State changes (deployed → failed → deployed)
  → Configuration drift detection
```

### Local GGUF Model Support
- **Offline-first** - All inference runs locally on C:/D:/ drives
- **Auto-discovery** - Scans standard paths for .gguf files
- **Model hot-swapping** - Loads/unloads models based on task
- **VRAM-aware** - Manages GPU memory for large models



## Current System Status

**Last Scan**: 2026-03-05 18:28
**Scan Script**: `deep_system_scan.py`

### Hardware
- **CPU**: AMD64 Family 25 Model 97 @ ~4501 MHz
- **RAM**: 130 GB Total (88 GB Available)
- **OS**: Windows 11 Pro (Build 26200)
- **Architecture**: x64-based PC

### Software
- **Python**: 3.13.7 (400+ packages)
- **Node.js**: v24.11.1
- **Docker**: 29.1.5
- **CUDA**: 13.1
- **Ollama**: 0.17.5

### GGUF Models
- **Total Models**: 58 files
- **Total Storage**: 257.06 GB
- **Key Models**:
  - Mistral-7B-Instruct-v0.2 (4.07 GB) - Master Agent
  - Llama-3.2-3B-Uncensored (multiple) - Analyzer/Deploy
  - Mistral-Small-24B (13.35 GB) - Complex Tasks
  - Qwen3-Coder-30B (30.25 GB) - Code Analysis

### Project Status
- **GitHub Repos**: 72 (100% synced)
- **Deployment Ready**: 34 projects
- **Needs Config**: 11 projects
- **Minimal**: 27 projects

> **Auto-Updated**: This section updates automatically on each system scan.
> Run `python deep_system_scan.py` to refresh.

---

---


## Current System Status

**Last Scan**: 2026-03-05 18:29
**Scan Script**: `deep_system_scan.py`

### Hardware
- **CPU**: AMD64 Family 25 Model 97 @ ~4501 MHz
- **RAM**: 130 GB Total (88 GB Available)
- **OS**: Windows 11 Pro (Build 26200)
- **Architecture**: x64-based PC

### Software
- **Python**: 3.13.7 (400+ packages)
- **Node.js**: v24.11.1
- **Docker**: 29.1.5
- **CUDA**: 13.1
- **Ollama**: 0.17.5

### GGUF Models
- **Total Models**: 58 files
- **Total Storage**: 257.06 GB
- **Key Models**:
  - Mistral-7B-Instruct-v0.2 (4.07 GB) - Master Agent
  - Llama-3.2-3B-Uncensored (multiple) - Analyzer/Deploy
  - Mistral-Small-24B (13.35 GB) - Complex Tasks
  - Qwen3-Coder-30B (30.25 GB) - Code Analysis

### Project Status
- **GitHub Repos**: 72 (100% synced)
- **Deployment Ready**: 34 projects
- **Needs Config**: 11 projects
- **Minimal**: 27 projects

> **Auto-Updated**: This section updates automatically on each system scan.
> Run `python deep_system_scan.py` to refresh.

---

## Quick Start

### Prerequisites

```bash
# Python 3.10+
pip install -r requirements.txt

# Install llama-cpp-python with CUDA support (optional)
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
```

### Model Setup

Place GGUF models in any of these locations:
```
C:/models/
C:/models/gguf/
D:/models/
D:/models/gguf/
D:/AI/models/
```

Recommended models:
- **Master**: `mistral-7b-instruct-v0.2.Q4_K_M.gguf`
- **Analyzer**: `phi-3-mini-4k-instruct.Q4_K_M.gguf`
- **Deploy**: `llama-3.2-1b-instruct.Q4_K_M.gguf`

### Configuration

```bash
# GitHub token (for private repos and higher rate limits)
export GITHUB_TOKEN=ghp_your_token_here

# Optional: CUDA for GPU acceleration
export GGML_CUDA=1
```

### Running the System

```bash
# Start the API server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Access dashboard at http://localhost:8000
```

### Workflow Example

```bash
# 1. Scan for available models
curl http://localhost:8000/api/models/scan

# 2. Scan GitHub user for profitable repos
curl -X POST http://localhost:8000/api/github/scan \
  -H "Content-Type: application/json" \
  -d '{"username": "caseboybelize501", "min_profit_score": 5.0}'

# 3. View created jobs
curl http://localhost:8000/api/jobs

# 4. Process job queue (Master Agent decides + executes)
curl -X POST http://localhost:8000/api/jobs/process-queue

# 5. Check job status
curl http://localhost:8000/api/jobs/{job_id}/status
```

## API Endpoints

### Model Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models/scan` | POST | Scan C:/D:/ for GGUF models |
| `/api/models/status` | GET | Get loaded model status |

### GitHub Scanning
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/github/scan` | POST | Scan user repos, create jobs for profitable ones |
| `/api/github/user/{username}/repos` | GET | List all user repositories |

### Job Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | GET | List all jobs (filter by status) |
| `/api/jobs/{job_id}` | GET | Get job details |
| `/api/jobs/{job_id}/decide` | POST | Run Master Agent decision on job |
| `/api/jobs/process-queue` | POST | Process all pending jobs |
| `/api/jobs/queue/status` | GET | Get queue status |

### Deployment
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/deploy/start` | POST | Start deployment for repo |
| `/api/deploy/{job_id}/status` | GET | Get deployment status |

### Memory
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/memory/summary` | GET | Memory system summary |
| `/api/memory/{repo_name}` | GET | All memory for specific repo |
| `/api/memory/drift/summary` | GET | Drift tracking summary |
| `/api/memory/{repo_name}/should-process` | GET | Check if repo should be processed |

## Project Structure

```
open.host/
├── src/
│   ├── main.py                      # FastAPI application + orchestration
│   ├── models.py                    # Pydantic models
│   ├── llm/
│   │   ├── model_pool.py            # GGUF model discovery + management
│   │   ├── llm_engine.py            # Local LLM inference engine
│   │   └── __init__.py
│   ├── github/
│   │   ├── github_scanner.py        # GitHub API integration
│   │   └── __init__.py
│   ├── agents/
│   │   ├── master_agent.py          # Master orchestrator (large model)
│   │   ├── analyzer_agent.py        # Code analysis (small model)
│   │   ├── deploy_agent.py          # Deployment execution
│   │   ├── memory_agent.py          # 4-layer memory + drift
│   │   ├── platform_agent.py        # Platform matching
│   │   ├── project_agent.py         # Project analysis
│   │   ├── validate_agent.py        # Validation orchestration
│   │   └── learn_agent.py           # Learning from outcomes
│   ├── bootstrap/
│   │   ├── system_scanner.py        # System bootstrap
│   │   ├── tool_scanner.py          # Tool detection
│   │   ├── platform_scanner.py      # Platform detection
│   │   ├── credential_scanner.py    # Credential detection
│   │   └── system_profile.py        # System profile
│   ├── deployment/
│   │   ├── netlify_deploy.py
│   │   ├── vercel_deploy.py
│   │   ├── github_pages_deploy.py
│   │   └── render_deploy.py
│   ├── validation/
│   │   ├── cycle_manager.py         # 10-stage × 7 consecutive
│   │   ├── lighthouse_runner.py
│   │   ├── health_check.py
│   │   └── functional_tests.py
│   ├── testing/
│   │   └── mutation_injector.py     # Mutation testing
│   └── memory/
│       ├── deployment_failure_store.py  # Layer 1 (ChromaDB)
│       ├── project_pattern_graph.py     # Layer 2 (Neo4j)
│       ├── platform_library.py          # Layer 3
│       └── meta_learner.py              # Layer 4 (sklearn)
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── pages/
│           ├── Dashboard.jsx
│           ├── DeploymentHistory.jsx
│           └── MemoryView.jsx
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Profitability Scoring

Repos are scored 0-10 based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Stars** | +2 for >100, +1 for >10 | Community validation |
| **Recent Activity** | +2 for <30d, +1 for <90d | Active maintenance |
| **Tech Stack** | +1-3 | Deployable technologies |
| **Has Pages** | +1 | Already deployed |
| **Not Fork** | Required | Original content only |
| **Not Archived** | Required | Active projects only |

**Threshold**: Score ≥ 5.0 = Profitable (eligible for deployment)

## Drift Tracking

The Memory Agent tracks state changes over time:

```python
# Example drift detection
{
    "repo_name": "my-react-app",
    "drift_type": "profitability",
    "previous_value": 7.5,
    "current_value": 4.2,
    "drift_magnitude": 0.33,
    "significant": True,
    "timestamp": "2024-01-15T10:30:00"
}
```

Significant drift (>0.3) triggers:
- Re-evaluation of deployment status
- Memory update across all 4 layers
- Potential job cancellation

## Supported Platforms

| Platform | Project Types | Free Tier |
|----------|--------------|-----------|
| **Netlify** | Static, React, Vue, Angular, Svelte, Gatsby, Nuxt | 100GB/month |
| **Vercel** | Static, React, Next.js, Vue, Nuxt, Remix, Gatsby | 100GB/month |
| **GitHub Pages** | Static sites | Unlimited |
| **Render** | Node, Python, Docker, Go, Rust | Unlimited bandwidth |

## Development

### Adding New Model Support

```python
from src.llm.model_pool import get_model_pool

pool = get_model_pool()
pool.scan_paths.append(Path("E:/new-models"))
models = pool.scan_for_models()
```

### Custom Profitability Criteria

```python
from src.agents.memory_agent import get_memory_agent

memory = get_memory_agent()
memory.profitability_window = 60  # Days
memory.drift_threshold = 0.25  # More sensitive
```

## License

MIT

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.
