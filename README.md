# ◈ Synapse — AI Answer Engine

An AI-powered search platform built with **FastAPI + Google Gemini**. Ask any question, get a web-informed AI answer, then compare it against your own expected answer to get a detailed accuracy score.

---

## ✨ Features

- 🌐 **Web Search** — Uses DuckDuckGo to fetch real-time context (no API key needed)
- 🤖 **Google Gemini** — Generates intelligent answers using web context
- 📝 **Your Answer Tab** — Input what you expected the answer to be
- 📊 **AI Scoring** — Compares AI answer vs your answer across 4 dimensions
- 🎯 **Verdict System** — Excellent / Good / Acceptable / Poor rating with detailed feedback

---

## 📁 Project Structure

```
synapse/
├── api/
│   └── index.py          # FastAPI backend (Vercel serverless)
├── templates/
│   └── index.html        # Frontend UI
├── vercel.json           # Vercel deployment config
├── requirements.txt      # Python dependencies
├── .gitignore
└── README.md
```

---

## 🚀 Deploy to Vercel (Step by Step)

### Step 1 — Get Your Free Gemini API Key

1. Go to → [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy and save the key somewhere safe

> ⚠️ Never put your API key directly in the code. We'll add it as an environment variable.

---

### Step 2 — Push Code to GitHub

Make sure your folder looks like the structure above, then run these commands in your terminal inside the project folder:

```bash
git init
git add .
git commit -m "Initial commit - Synapse AI Search"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/synapse-ai-search.git
git push -u origin main
```

> Replace `YOUR_USERNAME` with your actual GitHub username.
> If you get `error: remote origin already exists`, run:
> `git remote remove origin` then add it again.

---

### Step 3 — Deploy on Vercel

1. Go to → [https://vercel.com](https://vercel.com)
2. Click **"Sign Up"** → choose **"Continue with GitHub"**
3. After login, click **"Add New..."** → **"Project"**
4. Find your `synapse-ai-search` repository → click **"Import"**
5. Leave all settings as default (Vercel auto-detects everything)
6. Click **"Deploy"**
7. Wait ~1 minute for the build to complete

---

### Step 4 — Add Your Gemini API Key

> ⚠️ This step is required — without it the app won't work.

1. On your Vercel project dashboard, click **"Settings"** (top menu)
2. Click **"Environment Variables"** (left sidebar)
3. Fill in:
   - **Name:** `GEMINI_API_KEY`
   - **Value:** `your_actual_gemini_key_here`
   - **Environment:** Select all three (Production, Preview, Development)
4. Click **"Save"**
5. Go back to **"Deployments"** tab → click the three dots `...` on the latest deployment → click **"Redeploy"**

---

### Step 5 — Open Your Live App 🎉

Your app will be live at:
```
https://synapse-ai-search.vercel.app
```
(or a similar URL shown on your Vercel dashboard)

---

## 🔁 How to Update Your App

Whenever you make changes to your code locally, just push to GitHub:

```bash
git add .
git commit -m "describe your changes"
git push
```

Vercel automatically detects the push and redeploys within ~1 minute. ✨

---

## 📊 Scoring Dimensions

Each answer is scored out of 100 across 4 dimensions:

| Dimension | Max Points | What It Checks |
|---|---|---|
| Factual Accuracy | 25 | Is the AI answer factually correct? |
| Completeness | 25 | Did it cover what you expected? |
| Relevance | 25 | Did it stay on topic? |
| Clarity | 25 | Was it well explained? |

---

## 🔧 Running Locally (Optional)

If you want to test on your own computer before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export GEMINI_API_KEY="your_key_here"   # Mac/Linux
set GEMINI_API_KEY=your_key_here        # Windows

# Run the server
uvicorn api.index:app --reload --port 8000
```

Then open → [http://localhost:8000](http://localhost:8000)

> Note: Add `uvicorn` to requirements for local use: `pip install uvicorn`

---

## 🆘 Troubleshooting

| Problem | Fix |
|---|---|
| App shows "GEMINI_API_KEY is not set" | Add the env variable in Vercel Settings → redeploy |
| Build fails on Vercel | Check that `vercel.json` and `api/index.py` exist |
| 500 error on search | Check Vercel function logs in the dashboard |
| Gemini API error | Verify your API key is valid at aistudio.google.com |
| Templates not found | Make sure `templates/index.html` is in the repo |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| AI Model | Google Gemini 2.0 Flash (Free tier) |
| Web Search | DuckDuckGo Instant Answer API (Free, no key) |
| Serverless Adapter | Mangum |
| Hosting | Vercel (Free tier) |
| Frontend | Vanilla HTML + CSS + JS |

---

## 📄 License

MIT — free to use and modify.
