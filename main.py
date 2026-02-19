from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os
import json
from pydantic import BaseModel
from typing import Optional

# Compatible with pydantic v1
import urllib.parse

app = FastAPI(title="AI Search Platform")
templates = Jinja2Templates(directory="templates")

# ── CONFIG ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Free web search via DuckDuckGo Instant Answer API (no key needed)
DDGO_SEARCH_URL = "https://api.duckduckgo.com/"

# ── MODELS ──────────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    expected_answer: Optional[str] = None

class ScoreRequest(BaseModel):
    query: str
    ai_answer: str
    expected_answer: str

# ── HELPERS ─────────────────────────────────────────────────────────────────
async def web_search(query: str) -> str:
    """Fetch DuckDuckGo snippets for context."""
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(DDGO_SEARCH_URL, params=params)
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
    """Call Gemini API with a prompt."""
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
            return "No response from Gemini."
        except Exception as e:
            return f"Request failed: {str(e)}"


# ── ROUTES ──────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/search")
async def search(req: SearchRequest):
    # 1. Get web context
    web_context = await web_search(req.query)

    # 2. Ask Gemini with web context
    prompt = f"""You are a helpful AI assistant with access to the following web search results for context.

Web Search Context:
{web_context}

User Question: {req.query}

Please provide a comprehensive, accurate answer based on the web context and your knowledge. 
Be concise but complete. Format your answer in clear paragraphs."""

    ai_answer = await call_gemini(prompt)

    return JSONResponse({
        "ai_answer": ai_answer,
        "web_context": web_context,
        "query": req.query
    })


@app.post("/score")
async def score(req: ScoreRequest):
    """Compare AI answer vs user's expected answer and return a score."""
    scoring_prompt = f"""You are an expert answer evaluator. Compare the AI-generated answer with the user's expected answer for the given question.

Question: {req.query}

AI Answer:
{req.ai_answer}

User's Expected Answer:
{req.expected_answer}

Evaluate on these 4 dimensions (each 0-25 points):
1. Factual Accuracy (0-25): Is the AI answer factually correct?
2. Completeness (0-25): Does the AI answer cover what was expected?
3. Relevance (0-25): Does the AI answer address the question directly?
4. Clarity (0-25): Is the AI answer well-explained?

Respond ONLY with valid JSON in this exact format (no markdown):
{{
  "total_score": <number 0-100>,
  "factual_accuracy": <number 0-25>,
  "completeness": <number 0-25>,
  "relevance": <number 0-25>,
  "clarity": <number 0-25>,
  "verdict": "<one of: Excellent | Good | Acceptable | Poor>",
  "feedback": "<2-3 sentences explaining the score and key differences>",
  "matches_expected": <true or false>
}}"""

    raw = await call_gemini(scoring_prompt)

    # Try to parse JSON from Gemini response
    try:
        # Strip markdown code blocks if present
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        score_data = json.loads(clean.strip())
    except Exception:
        score_data = {
            "total_score": 50,
            "factual_accuracy": 13,
            "completeness": 13,
            "relevance": 12,
            "clarity": 12,
            "verdict": "Acceptable",
            "feedback": "Could not parse detailed scoring. Raw response: " + raw[:200],
            "matches_expected": False
        }

    return JSONResponse(score_data)


@app.get("/health")
async def health():
    return {"status": "ok", "gemini_key_set": GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE"}
