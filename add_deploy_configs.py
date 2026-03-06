"""
Add deployment configs to cog-load
"""
import os

workspace = "D:/projects/open-host-workspace/cog-load"

# render.yaml
render_yaml = """services:
  - type: web
    name: cog-load
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python daemon/main.py
    healthCheckPath: /health
    healthCheckTimeout: 30
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.16
      - key: FLASK_ENV
        value: production
"""

# Dockerfile
dockerfile = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "daemon/main.py"]
"""

# Procfile (for Heroku-style deploys)
procfile = """web: python daemon/main.py
"""

# .dockerignore
dockerignore = """__pycache__/
*.pyc
.git
.env
*.md
"""

files = {
    "render.yaml": render_yaml,
    "Dockerfile": dockerfile,
    "Procfile": procfile,
    ".dockerignore": dockerignore
}

for filename, content in files.items():
    path = os.path.join(workspace, filename)
    with open(path, 'w') as f:
        f.write(content)
    print(f"[OK] Created {filename}")

print("\n[OK] All deployment configs created!")
