# Open.Host Jarvis

**Autonomous Open Source Hosting Finder**

A self-learning system that autonomously discovers, deploys to, and validates hosting platforms for your projects.

## Features

- **System Scan**: Detects installed tools and project types
- **Platform Discovery**: Scans available free hosting platforms
- **Auto Deployment**: Deploys with zero configuration
- **10-Stage Validation**: Ensures production readiness
- **Self-Learning**: Builds a library of platform-project compatibility

## Architecture


[Voice/Chat] → [Planner LLM] → [Agent Controller]
    ↓
[Project Agent] → [Platform Agent] → [Deploy Agent] → [Validate Agent] → [Learn Agent]
    ↓
[Tools] + [Memory] + [APIs]


## Quick Start

bash
# Install dependencies
pip install -r requirements.txt

# Run the system
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Access dashboard at http://localhost:8000


## System Components

- **Bootstrap**: Tool detection, project analysis, platform scan, credential scan
- **Agents**: Project, Platform, Deploy, Validate, Learn
- **Deployment**: Netlify, Vercel, GitHub Pages, Render
- **Validation**: 10-stage cycle with mutation testing
- **Memory**: Failure patterns, project graphs, build strategies, meta-learning

## License

MIT
