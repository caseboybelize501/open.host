# Deployment Guide - cog-load
## Cognitive Load Operating System

## Free Hosting Options

### Option 1: Render (Recommended for Python + Flask)

**Why Render:**
- Free tier with unlimited bandwidth
- Supports Python/Flask natively
- Auto-deploys from GitHub
- Includes PostgreSQL/Redis add-ons

**Setup Steps:**

1. Create `render.yaml` in project root:
```yaml
services:
  - type: web
    name: cog-load
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python daemon/main.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.16
      - key: FLASK_ENV
        value: production
```

2. Push to GitHub (already done)

3. Deploy on Render:
   - Go to https://render.com
   - Click "New +" → "Blueprint"
   - Connect GitHub repo: `caseboybelize501/cog-load`
   - Deploy!

**Free Tier Limits:**
- 750 hours/month (enough for 1 instance running 24/7)
- 512MB RAM
- Shared CPU

---

### Option 2: Railway

**Why Railway:**
- $5 free credit/month
- Easy GitHub integration
- Includes Redis

**Setup:**
1. Go to https://railway.app
2. "New Project" → "Deploy from GitHub"
3. Select `cog-load` repo
4. Add Redis plugin
5. Deploy

---

### Option 3: Fly.io

**Why Fly.io:**
- 3 shared VMs free
- Global edge locations
- Docker support

**Setup:**
```bash
# Install flyctl
curl -L https://fly.io/sh/install.sh | sh

# Login
flyctl auth login

# Deploy
cd D:\projects\open-host-workspace\cog-load
flyctl launch --generate-name
flyctl deploy
```

---

## Pre-Deployment Checklist

- [x] Dependencies installed
- [ ] Redis configured (optional for local)
- [ ] Environment variables set
- [ ] Health check endpoint working
- [ ] GitHub repo up to date

## Environment Variables

```bash
# Required
FLASK_ENV=production
SECRET_KEY=<generate-random-key>

# Optional
REDIS_URL=redis://localhost:6379
LLAMA_API_URL=http://localhost:8080
```

## Post-Deployment

Test the deployment:
```bash
curl https://<your-app>.onrender.com/health
curl https://<your-app>.onrender.com/api/state/current
```

## Monitoring

- Render Dashboard: https://dashboard.render.com
- Logs: `render logs <service-name>`
- Metrics: Available in dashboard

---

**Next Steps:**
1. Choose hosting platform
2. Create deployment config file
3. Push to GitHub
4. Deploy!
