from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from mangum import Mangum
import httpx
import os
import json
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

app = FastAPI(title="Synapse AI Search")

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ── CONFIG ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DDGO_URL = "https://api.duckduckgo.com/"

# ── MODELS ───────────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str

class ScoreRequest(BaseModel):
    query: str
    ai_answer: str
    expected_answer: str

# ── HELPERS ──────────────────────────────────────────────────────────────────
async def web_search(query: str) -> str:
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(DDGO_URL, params=params)
            data = r.json()
            snippets = []
            if data.get("AbstractText"):
                snippets.append(data["AbstractText"])
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    snippets.append(topic["Text"])
            return "\n".join(snippets) if snippets else "No web results found."
        except Exception as e:
            return f"Web search error: {str(e)}"


async def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY is not set. Please add it in Vercel environment variables."
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024}
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                headers=headers,
                json=body
            )
            data = r.json()
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            elif "error" in data:
                return f"Gemini API Error: {data['error'].get('message', 'Unknown error')}"
            return "No response received from Gemini."
        except Exception as e:
            return f"Request failed: {str(e)}"


# ── ROUTES ───────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/search")
async def search(req: SearchRequest):
    web_context = await web_search(req.query)
    prompt = f"""You are a helpful AI assistant with access to web search results.

Web Search Context:
{web_context}

User Question: {req.query}

Provide a comprehensive, accurate answer based on the context and your knowledge. Be concise but complete. Write in clear paragraphs."""

    ai_answer = await call_gemini(prompt)
    return JSONResponse({
        "ai_answer": ai_answer,
        "web_context": web_context,
        "query": req.query
    })


@app.post("/score")
async def score(req: ScoreRequest):
    prompt = f"""You are an expert answer evaluator. Compare the AI-generated answer with the user's expected answer for the given question.

Question: {req.query}

AI Answer:
{req.ai_answer}

User's Expected Answer:
{req.expected_answer}

Score on 4 dimensions (each 0-25 points):
1. Factual Accuracy (0-25): Is the AI answer factually correct?
2. Completeness (0-25): Does it cover what was expected?
3. Relevance (0-25): Does it address the question directly?
4. Clarity (0-25): Is it well-explained?

Respond ONLY with valid JSON, no markdown backticks:
{{
  "total_score": <0-100>,
  "factual_accuracy": <0-25>,
  "completeness": <0-25>,
  "relevance": <0-25>,
  "clarity": <0-25>,
  "verdict": "<Excellent|Good|Acceptable|Poor>",
  "feedback": "<2-3 sentences explaining score and key differences>",
  "matches_expected": <true|false>
}}"""

    raw = await call_gemini(prompt)
    try:
        clean = raw.strip()
        if "```" in clean:
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        result = json.loads(clean.strip())
    except Exception:
        result = {
            "total_score": 50, "factual_accuracy": 13, "completeness": 13,
            "relevance": 12, "clarity": 12, "verdict": "Acceptable",
            "feedback": "Scoring could not be parsed. Please try again.",
            "matches_expected": False
        }
    return JSONResponse(result)


@app.get("/health")
async def health():
    return {"status": "ok", "gemini_configured": bool(GEMINI_API_KEY)}


# Vercel serverless handler
handler = Mangum(app)
