# 📘 Setup & Deployment Guide

## Prerequisites
- GitHub account
- Streamlit Cloud account (free) — [share.streamlit.io](https://share.streamlit.io)
- Python 3.11+ (for local testing only)

---

## Step 1: GitHub Repository Setup

1. Create a new GitHub repository named `domain-intelligence-app`
2. Push all project files to the repository:

```bash
cd domain-intelligence-app
git init
git add .
git commit -m "Initial commit: Domain Intelligence App"
git remote add origin https://github.com/YOUR_USERNAME/domain-intelligence-app.git
git branch -M main
git push -u origin main
```

3. **Enable GitHub Actions**:
   - Go to repo → Settings → Actions → General
   - Select "Allow all actions and reusable workflows"
   - Under "Workflow permissions", select **Read and write permissions**
   - Click Save

---

## Step 2: Run Pipeline (First Time)

Run locally to generate initial data:

```bash
pip install -r requirements.txt
python -m pipeline.run_pipeline
```

Then commit the generated data:

```bash
git add data/
git commit -m "Add initial scored dataset"
git push
```

---

## Step 3: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your GitHub repository
4. Set these fields:
   - **Repository**: `YOUR_USERNAME/domain-intelligence-app`
   - **Branch**: `main`
   - **Main file path**: `app/app.py`
5. Click **Deploy**

Your dashboard will be live at: `https://YOUR_APP.streamlit.app`

---

## Step 4: Verify Automation

1. Go to your GitHub repo → **Actions** tab
2. You should see the "Domain Intelligence Daily Pipeline" workflow
3. Click **"Run workflow"** → **"Run workflow"** to test manually
4. Verify it completes successfully and commits updated data

The workflow will now run automatically every day at 6 AM UTC.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Pipeline fails with import errors | Ensure `PYTHONPATH` includes project root |
| No data in dashboard | Run `python -m pipeline.run_pipeline` locally first |
| GitHub Actions permissions error | Enable "Read and write permissions" in repo settings |
| Streamlit shows error | Check that `data/domains.csv` exists in the repo |
| pytrends rate limited | System falls back to static scoring automatically |

---

## Scaling Suggestions

| Current | Future Upgrade |
|---------|---------------|
| CSV in GitHub | PostgreSQL via Supabase (free tier) |
| Seed data | ICANN CZDS zone files (apply for access) |
| Static trend scores | Real-time pytrends with Redis caching |
| Streamlit Cloud | Next.js + Vercel for custom UI |
| GitHub Actions | Temporal or Airflow for complex orchestration |
| Heuristic pricing | GoDaddy GoValue API or DomScan free tier |
