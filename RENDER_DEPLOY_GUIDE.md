# Render Deployment Guide

## Quick Redeploy (After Fixing Issues)

### If Already Deployed (Auto-redeploy on push)
1. Fix the issue locally (e.g., `requirements.txt`)
2. Commit and push:
   ```bash
   git add .
   git commit -m "Fix: description"
   git push origin master
   ```
3. Render auto-redeploys in 1-2 minutes
4. Check logs at: https://dashboard.render.com → Your Service → Logs

### Manual Redeploy
1. Go to https://dashboard.render.com
2. Click your service (e.g., `daw`)
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

### Cancel and Start Fresh
1. Dashboard → Your service
2. Settings → Scroll to bottom
3. **"Delete Service"** (red button)
4. Redeploy via Blueprint

---

## Automated Deployment (API)

### Get API Key
1. Go to https://dashboard.render.com/u/settings/api
2. Click **"Create API Key"**
3. Copy the key (starts with `rnd_...`)

### Set Environment Variable
```bash
# Windows (Command Prompt)
set RENDER_API_KEY=rnd_your_key_here

# Windows (PowerShell)
$env:RENDER_API_KEY="rnd_your_key_here"

# Linux/Mac
export RENDER_API_KEY=rnd_your_key_here
```

### Run Automated Deploy
```bash
cd d:\Users\CASE\projects\open.host
python deploy_to_render.py
```

### List Existing Services
```bash
python deploy_to_render.py --list
```

### Deploy Specific Projects
Edit `deploy_to_render.py` and modify the `TIER1_PROJECTS` list:
```python
TIER1_PROJECTS = [
    {'repo': 'daw', 'name': 'daw', 'branch': 'master'},
    # Add/remove projects here
]
```

---

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/services` | GET | List all services |
| `/v1/blueprints/deploy` | POST | Create service from Blueprint |
| `/v1/deploys` | POST | Trigger manual deploy |
| `/v1/deploys/{id}` | GET | Check deploy status |
| `/v1/services/{id}` | DELETE | Delete service |

---

## Troubleshooting

### "Service already exists"
- The script will auto-redeploy instead of failing
- Or delete the old service first

### "Blueprint not found"
- Ensure `render.yaml` exists in repo root
- Check branch name is correct (usually `master`)

### "Rate limited"
- Render limits API calls
- Script includes 2-second delay between deploys

### Build fails with "package not found"
- Run `python validate_deploy.py` first
- Fix issues locally before deploying

---

## Full Workflow (Recommended)

```bash
# 1. Validate all projects locally
python validate_deploy.py

# 2. Fix any issues (offline)
cd <project-name>
# Edit files...
git add/push

# 3. Re-validate
python validate_deploy.py  # Should show 100% pass

# 4. Deploy to Render
python deploy_to_render.py

# 5. Monitor at https://dashboard.render.com
```

---

## Cost Estimates (Free Tier)

| Service Type | Free Tier | Overage |
|-------------|-----------|---------|
| Web Service | 750 hours/month | $7/month |
| Static Site | 100GB bandwidth | $7/month |
| Database | 256MB RAM | $7/month |

**750 hours = 1 service running 24/7**
- Deploy 10 services = ~75 hours each (3 days)
- Or run services on-demand (sleep after inactivity)

---

## Support

- Render Docs: https://docs.render.com
- API Docs: https://api-docs.render.com
- Discord: https://discord.gg/render
