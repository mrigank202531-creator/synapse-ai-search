# ◈ Synapse — AI Answer Engine

AI-powered search platform. Ask any question, get a Gemini-powered answer with web context, then score it against your own expected answer.

---

## 📁 Project Structure

```
synapse/
├── api/
│   └── index.py      ← entire backend + frontend (single file)
├── vercel.json       ← Vercel config
├── requirements.txt  ← Python dependencies
└── .gitignore
```

> No `templates/` folder needed — HTML is served directly from Python to avoid path issues on Vercel.

---

## 🚀 Deploy to Vercel

### Step 1 — Get Free Gemini API Key
1. Go to → https://aistudio.google.com/app/apikey
2. Click **"Create API Key"** (free, no credit card)
3. Copy the key

### Step 2 — Push to GitHub
```bash
git init
git add .
git commit -m "Synapse AI Search"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/synapse-ai-search.git
git push -u origin main
```

### Step 3 — Deploy on Vercel
1. Go to → https://vercel.com → sign in with GitHub
2. Click **"Add New"** → **"Project"**
3. Import your `synapse-ai-search` repo
4. Leave all settings default → click **"Deploy"**

### Step 4 — Add API Key (Required)
1. Vercel dashboard → **"Settings"** → **"Environment Variables"**
2. Add:
   - Name: `GEMINI_API_KEY`
   - Value: your Gemini key
   - Environments: ✅ Production ✅ Preview ✅ Development
3. Click **"Save"**
4. Go to **"Deployments"** → click `...` → **"Redeploy"**

### Step 5 — Done! 🎉
Your app is live at: `https://synapse-ai-search.vercel.app`

---

## 🔁 Update Your App
```bash
git add .
git commit -m "your change"
git push
```
Vercel auto-redeploys on every push.

---

## 📊 Scoring System

| Dimension | Max | What It Checks |
|---|---|---|
| Factual Accuracy | 25 | Is the AI factually correct? |
| Completeness | 25 | Did it cover what was expected? |
| Relevance | 25 | Did it stay on topic? |
| Clarity | 25 | Was it well explained? |

---

## 🆘 Troubleshooting

| Problem | Fix |
|---|---|
| 500 FUNCTION_INVOCATION_FAILED | Check Vercel logs → likely missing env variable |
| "GEMINI_API_KEY not set" error | Add it in Vercel Settings → Environment Variables → Redeploy |
| Gemini API error | Verify key at aistudio.google.com |
| Build fails | Make sure `api/index.py` and `vercel.json` exist |

---

## 🛠️ Tech Stack
- **Backend:** FastAPI + Mangum (serverless adapter)
- **AI:** Google Gemini 2.0 Flash (free tier)
- **Web Search:** DuckDuckGo (free, no key needed)
- **Hosting:** Vercel (free tier)
- **Frontend:** Vanilla HTML/CSS/JS (inlined in Python)
