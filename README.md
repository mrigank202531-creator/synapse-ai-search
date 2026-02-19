# ◈ Synapse — AI Answer Engine

AI-powered search + answer scoring platform using FastAPI + Google Gemini.

---

## 📁 Project Structure

```
synapse/
├── api/
│   └── index.py       ← entire app (backend + inlined HTML)
├── vercel.json        ← Vercel routing config
├── requirements.txt   ← minimal dependencies
└── .gitignore
```

---

## 🚀 Deploy to Vercel (Step by Step)

### Step 1 — Get Free Gemini API Key
1. Go to → https://aistudio.google.com/app/apikey
2. Click **"Create API Key"** (free, no credit card)
3. Copy the key

### Step 2 — Push to GitHub
```bash
git init
git add .
git commit -m "Synapse AI Search - final"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/synapse-ai-search.git
git push -u origin main
```
> If you get `error: remote origin already exists`:
> `git remote remove origin` then run the remote add line again.

### Step 3 — Deploy on Vercel
1. Go to → https://vercel.com → sign in with GitHub
2. Click **"Add New"** → **"Project"**
3. Import your `synapse-ai-search` repo
4. Leave all settings as default → click **"Deploy"**

### Step 4 — Add Gemini API Key ⚠️ Required
1. Vercel dashboard → **"Settings"** → **"Environment Variables"**
2. Add:
   - Name: `GEMINI_API_KEY`
   - Value: `your_key_here`
   - Check all 3 environments: Production, Preview, Development
3. Click **"Save"**
4. Go to **"Deployments"** → click `...` on latest → **"Redeploy"**

### Step 5 — Done 🎉
Live at: `https://synapse-ai-search.vercel.app`

---

## 🔁 Update App
```bash
git add .
git commit -m "your change"
git push
```
Vercel auto-redeploys on every push.

---

## 🐛 Error Reference: FUNCTION_INVOCATION_FAILED

This error means the Python serverless function crashed at **runtime** (not at build time).

### Root Causes We Fixed

**1. Mangum was unnecessary and caused crashes**
- Mangum is an adapter that wraps FastAPI for AWS Lambda
- Vercel's Python runtime natively supports ASGI/FastAPI — it does NOT need Mangum
- Adding Mangum introduced a conflict between Vercel's internal handler and the extra wrapper
- **Fix:** Removed Mangum entirely. Just expose `app = FastAPI()` and Vercel handles the rest

**2. Jinja2 template file paths broke in serverless**
- `Jinja2Templates(directory="templates")` resolves paths relative to the working directory
- On Vercel, the working directory inside a serverless function is unpredictable
- The file simply wasn't found → crash on every request
- **Fix:** Inlined the HTML directly into Python as a string — no file I/O needed

**3. Pinned dependency versions caused Rust compilation failures**
- `pydantic==2.x` requires compiling Rust code (pydantic-core)
- Vercel's build environment uses a read-only filesystem that blocks Rust's Cargo
- **Fix:** Use unpinned `fastapi` and `httpx` — Vercel installs the latest compatible versions with pre-built wheels

### How to Debug This Error in Future
1. Go to Vercel dashboard → your project → **"Logs"** tab
2. Look for the actual Python traceback — it will say exactly what crashed
3. Common patterns:
   - `ModuleNotFoundError` → missing package in requirements.txt
   - `FileNotFoundError` → don't use file I/O in serverless functions
   - `exit status 1` with no traceback → import error or compilation failure
   - `ValidationError` → missing environment variable

### Warning Signs to Watch For
- Using `open()`, file paths, or template directories in serverless code
- Pinning packages that require C/Rust compilation (check if package has `.tar.gz` only, no `.whl`)
- Adding adapter layers (Mangum, Gunicorn) that Vercel already handles internally
- Any package that needs to write to the filesystem at runtime

---

## 📊 Scoring Dimensions

| Dimension | Max | What It Checks |
|---|---|---|
| Factual Accuracy | 25 | Is the AI factually correct? |
| Completeness | 25 | Did it cover what was expected? |
| Relevance | 25 | Did it stay on topic? |
| Clarity | 25 | Was it well explained? |

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI | Modern, async, Vercel-native |
| AI | Google Gemini 2.0 Flash | Free tier, fast |
| Web Search | DuckDuckGo API | Free, no API key needed |
| Hosting | Vercel | Free, auto-deploy from GitHub |
| Frontend | Vanilla HTML/CSS/JS | Inlined in Python, zero file paths |

---

## 🆘 Troubleshooting

| Problem | Fix |
|---|---|
| FUNCTION_INVOCATION_FAILED | Check Vercel Logs tab for Python traceback |
| "GEMINI_API_KEY not set" shown in answer | Add env var in Settings → Redeploy |
| Gemini API error | Verify key at aistudio.google.com |
| Build fails | Ensure `api/index.py` and `vercel.json` are committed |
| Old version still showing | Hard refresh browser (Ctrl+Shift+R) |
