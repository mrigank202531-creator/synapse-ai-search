"""
Synapse AI Search — Vercel Python Serverless Function

KEY ARCHITECTURAL FACT:
Vercel's Python runtime calls vc_init.py which does:
    if not issubclass(handler_class, BaseHTTPRequestHandler): raise TypeError(...)

This means your exported 'handler' MUST be a class that extends
http.server.BaseHTTPRequestHandler. FastAPI/ASGI apps are NOT classes —
they are callable instances — so issubclass() raises TypeError and
the process exits with code 1 before serving a single request.
"""

from http.server import BaseHTTPRequestHandler
import json
import httpx
import os
from urllib.parse import urlparse

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DDGO_URL = "https://api.duckduckgo.com/"


# ── SYNC HELPERS (BaseHTTPRequestHandler is synchronous) ──────────────────────
def web_search(query: str) -> str:
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    try:
        r = httpx.get(DDGO_URL, params=params, timeout=10)
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


def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return (
            "⚠️ GEMINI_API_KEY is not set.\n\n"
            "To fix: Vercel Dashboard → Your Project → Settings → "
            "Environment Variables → Add GEMINI_API_KEY → Save → Redeploy."
        )
    try:
        r = httpx.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
            },
            timeout=30,
        )
        data = r.json()
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        if "error" in data:
            return f"Gemini API Error: {data['error'].get('message', 'Unknown')}"
        return "No response from Gemini."
    except Exception as e:
        return f"Request failed: {str(e)}"


# ── ROUTE HANDLERS ────────────────────────────────────────────────────────────
def handle_search(body: dict) -> dict:
    query = body.get("query", "").strip()
    if not query:
        return {"error": "Query is required"}
    ctx = web_search(query)
    answer = call_gemini(
        f"You are a helpful AI. Web context:\n{ctx}\n\nQuestion: {query}\n\n"
        "Provide a comprehensive, accurate answer in clear paragraphs."
    )
    return {"ai_answer": answer, "web_context": ctx, "query": query}


def handle_score(body: dict) -> dict:
    query = body.get("query", "")
    ai_answer = body.get("ai_answer", "")
    expected = body.get("expected_answer", "")
    if not all([query, ai_answer, expected]):
        return {"error": "Missing required fields: query, ai_answer, expected_answer"}

    raw = call_gemini(
        f"You are an expert evaluator.\n\n"
        f"Question: {query}\nAI Answer: {ai_answer}\nExpected: {expected}\n\n"
        "Score each dimension 0–25: Factual Accuracy, Completeness, Relevance, Clarity.\n"
        "Reply ONLY with JSON, no markdown:\n"
        '{"total_score":0,"factual_accuracy":0,"completeness":0,"relevance":0,'
        '"clarity":0,"verdict":"Good","feedback":"...","matches_expected":false}'
    )
    try:
        clean = raw.strip()
        if "```" in clean:
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except Exception:
        return {
            "total_score": 50, "factual_accuracy": 13, "completeness": 13,
            "relevance": 12, "clarity": 12, "verdict": "Acceptable",
            "feedback": "Score could not be parsed from AI response. Try again.",
            "matches_expected": False,
        }


# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Synapse — AI Answer Engine</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0a0a0f;--surface:#111118;--surface2:#1a1a24;--border:#ffffff12;--accent:#7c6dff;--accent2:#ff6b9d;--accent3:#00d4aa;--text:#e8e8f0;--muted:#6b6b80;--danger:#ff4d6d}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'DM Mono',monospace;overflow-x:hidden}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 80% 60% at 20% 10%,#7c6dff18 0%,transparent 60%),
             radial-gradient(ellipse 60% 50% at 80% 80%,#ff6b9d12 0%,transparent 60%)}
.wrap{position:relative;z-index:1;max-width:860px;margin:0 auto;padding:0 24px}
header{padding:40px 0 20px}
.logo{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;letter-spacing:-1px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.logo span{font-size:13px;color:var(--muted);-webkit-text-fill-color:var(--muted);font-family:'DM Mono',monospace;margin-left:8px;vertical-align:middle}
.tag{font-size:11px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-top:4px}
.sw{margin:48px 0 40px}
.sb{display:flex;align-items:center;background:var(--surface);border:1px solid var(--border);border-radius:16px;transition:border-color .3s,box-shadow .3s;overflow:hidden}
.sb:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px #7c6dff20}
.si{padding:0 16px 0 20px;color:var(--muted);font-size:18px}
#q{flex:1;background:transparent;border:none;outline:none;font-family:'DM Mono',monospace;font-size:15px;color:var(--text);padding:20px 0;caret-color:var(--accent)}
#q::placeholder{color:var(--muted)}
.sbtn{margin:8px;padding:12px 24px;background:linear-gradient(135deg,var(--accent),#9b8aff);border:none;border-radius:10px;color:#fff;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;cursor:pointer;transition:all .2s;white-space:nowrap}
.sbtn:hover{transform:translateY(-1px);box-shadow:0 8px 25px #7c6dff40}
.sbtn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.tabs{display:none}.tabs.on{display:block}
.tbar{display:flex;gap:4px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:4px;margin-bottom:20px;width:fit-content}
.tb{padding:10px 22px;border-radius:8px;border:none;background:transparent;color:var(--muted);font-family:'DM Mono',monospace;font-size:12px;cursor:pointer;transition:all .25s}
.tb.on{background:var(--surface2);color:var(--text);box-shadow:0 2px 12px #00000040}
.dot{display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:8px;background:var(--accent);vertical-align:middle}
.tb:nth-child(2) .dot{background:var(--accent2)}.tb:nth-child(3) .dot{background:var(--accent3)}
.tp{display:none}.tp.on{display:block}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:28px;margin-bottom:16px}
.pl{font-family:'Syne',sans-serif;font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:16px;display:flex;align-items:center;gap:8px}
.pl::before{content:'';display:inline-block;width:20px;height:1px;background:var(--accent)}
.ti{display:none;gap:4px;padding:20px 0;align-items:center}.ti.on{display:flex}
.ti span{width:6px;height:6px;background:var(--accent);border-radius:50%;animation:bounce 1.2s infinite}
.ti span:nth-child(2){animation-delay:.2s}.ti span:nth-child(3){animation-delay:.4s;background:var(--accent2)}
.ti .lbl{margin-left:10px;font-size:12px;color:var(--muted)}
.badge{display:inline-flex;align-items:center;gap:6px;background:#7c6dff15;border:1px solid #7c6dff30;border-radius:20px;padding:4px 12px;font-size:11px;color:var(--accent);margin-bottom:16px}
.ans{line-height:1.8;font-size:14px;color:var(--text);white-space:pre-wrap;word-break:break-word}
.ctx{font-size:12px;color:var(--muted);line-height:1.7;max-height:200px;overflow-y:auto;white-space:pre-wrap}
textarea{width:100%;background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:16px;color:var(--text);font-family:'DM Mono',monospace;font-size:13px;line-height:1.7;resize:vertical;min-height:140px;outline:none;transition:border-color .3s}
textarea:focus{border-color:var(--accent2)}textarea::placeholder{color:var(--muted)}
.scbtn{margin-top:16px;padding:14px 32px;width:100%;background:linear-gradient(135deg,var(--accent2),#ff8fab);border:none;border-radius:10px;color:#fff;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;cursor:pointer;transition:all .2s}
.scbtn:hover{transform:translateY(-1px);box-shadow:0 8px 25px #ff6b9d40}
.scbtn:disabled{opacity:.4;cursor:not-allowed;transform:none}
.sd{display:none}.sd.on{display:block}
.sh{display:flex;align-items:center;gap:32px;margin-bottom:28px;flex-wrap:wrap}
.sc{position:relative;width:110px;height:110px;flex-shrink:0}
.sc svg{transform:rotate(-90deg);width:110px;height:110px}
.sc .tr{fill:none;stroke:var(--surface2);stroke-width:8}
.sc .fi{fill:none;stroke-width:8;stroke-linecap:round;stroke-dasharray:283;stroke-dashoffset:283;transition:stroke-dashoffset 1.5s cubic-bezier(.22,1,.36,1)}
.sn{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-family:'Syne',sans-serif;font-size:28px;font-weight:800}
.vb{display:inline-block;padding:6px 16px;border-radius:20px;font-family:'Syne',sans-serif;font-size:13px;font-weight:700;margin-bottom:12px}
.sfb{font-size:13px;line-height:1.7;color:#b0b0c0}
.dims{display:grid;gap:12px}
.dr{display:flex;align-items:center;gap:12px}
.dl{font-size:11px;color:var(--muted);width:140px;flex-shrink:0;text-transform:uppercase;letter-spacing:.5px}
.dbw{flex:1;height:6px;background:var(--surface2);border-radius:3px;overflow:hidden}
.db{height:100%;border-radius:3px;width:0%;transition:width 1.2s cubic-bezier(.22,1,.36,1)}
.ds{font-size:12px;color:var(--text);width:30px;text-align:right}
.mb{display:inline-flex;align-items:center;gap:6px;font-size:11px;padding:4px 10px;border-radius:20px;margin-left:8px}
.my{background:#00d4aa15;border:1px solid #00d4aa30;color:var(--accent3)}
.mn{background:#ff4d6d15;border:1px solid #ff4d6d30;color:var(--danger)}
.empty{text-align:center;padding:80px 20px}
.empty .ic{font-size:48px;margin-bottom:16px;opacity:.4}
.empty h2{font-family:'Syne',sans-serif;font-size:22px;font-weight:700;margin-bottom:8px}
.empty p{font-size:13px;color:var(--muted);max-width:360px;margin:0 auto;line-height:1.7}
.pills{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:24px}
.pill{padding:6px 14px;border-radius:20px;border:1px solid var(--border);font-size:11px;color:var(--muted);background:var(--surface)}
.sph{text-align:center;padding:40px;color:var(--muted);font-size:13px;line-height:1.7}
@keyframes bounce{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-8px);opacity:1}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo">Synapse <span>// AI Answer Engine</span></div>
    <div class="tag">Search · Compare · Score · Verify</div>
  </header>
  <div class="sw">
    <div class="sb">
      <div class="si">⌕</div>
      <input id="q" type="text" placeholder="Ask anything... e.g. What is quantum entanglement?" autocomplete="off"/>
      <button class="sbtn" id="sb" onclick="doSearch()">Search →</button>
    </div>
  </div>
  <div class="empty" id="empty">
    <div class="ic">◈</div>
    <h2>AI-Powered Search with Answer Scoring</h2>
    <p>Ask any question. Provide your expected answer. Synapse uses Gemini + web search then scores how close the AI gets.</p>
    <div class="pills">
      <span class="pill">🌐 Web Search</span>
      <span class="pill">🤖 Google Gemini</span>
      <span class="pill">📊 Answer Scoring</span>
      <span class="pill">✓ Accuracy Check</span>
    </div>
  </div>
  <div class="tabs" id="tabs">
    <div class="tbar">
      <button class="tb on" onclick="sw('ai')"><span class="dot"></span>AI Answer</button>
      <button class="tb" onclick="sw('ex')"><span class="dot"></span>Your Answer</button>
      <button class="tb" onclick="sw('sc')"><span class="dot"></span>Score</button>
    </div>
    <div class="tp on" id="t-ai">
      <div class="panel">
        <div class="pl">Gemini Response</div>
        <div class="ti" id="ti"><span></span><span></span><span></span><span class="lbl">Searching web & generating answer...</span></div>
        <div id="ac"></div>
      </div>
      <div class="panel" id="cp" style="display:none">
        <div class="pl">Web Context Used</div>
        <div class="ctx" id="ct"></div>
      </div>
    </div>
    <div class="tp" id="t-ex">
      <div class="panel">
        <div class="pl">Your Expected Answer</div>
        <p style="font-size:12px;color:var(--muted);margin-bottom:16px;line-height:1.7">What answer were you expecting? This will be compared with the AI's answer to generate a score.</p>
        <textarea id="ea" placeholder="Type what you expected the AI to answer..."></textarea>
        <button class="scbtn" id="scb" onclick="doScore()" disabled>◈ Compare & Score →</button>
      </div>
    </div>
    <div class="tp" id="t-sc">
      <div class="panel">
        <div class="pl">Answer Analysis</div>
        <div id="sph" class="sph">Complete the <strong style="color:var(--text)">"Your Answer"</strong> tab first, then click Compare & Score.</div>
        <div class="sd" id="sd">
          <div class="sh">
            <div class="sc">
              <svg viewBox="0 0 100 100"><circle class="tr" cx="50" cy="50" r="45"/><circle class="fi" id="sf" cx="50" cy="50" r="45"/></svg>
              <div class="sn" id="snum">0</div>
            </div>
            <div style="flex:1">
              <div><span class="vb" id="vb">—</span><span class="mb" id="mb"></span></div>
              <div class="sfb" id="sfb"></div>
            </div>
          </div>
          <div class="dims" id="da"></div>
        </div>
      </div>
    </div>
  </div>
</div>
<script>
let ans='',qry='';
function sw(t){
  document.querySelectorAll('.tb').forEach((b,i)=>b.classList.toggle('on',['ai','ex','sc'][i]===t));
  document.querySelectorAll('.tp').forEach(p=>p.classList.remove('on'));
  document.getElementById('t-'+t).classList.add('on');
}
async function doSearch(){
  const q=document.getElementById('q').value.trim();
  if(!q)return;
  qry=q;ans='';
  document.getElementById('empty').style.display='none';
  document.getElementById('tabs').classList.add('on');
  sw('ai');
  document.getElementById('ti').classList.add('on');
  document.getElementById('ac').innerHTML='';
  document.getElementById('cp').style.display='none';
  document.getElementById('sb').disabled=true;
  document.getElementById('scb').disabled=true;
  document.getElementById('sd').classList.remove('on');
  document.getElementById('sph').style.display='block';
  document.getElementById('sph').innerHTML='Complete the <strong style="color:var(--text)">"Your Answer"</strong> tab first, then click Compare &amp; Score.';
  try{
    const r=await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})});
    const d=await r.json();
    document.getElementById('ti').classList.remove('on');
    if(d.ai_answer){
      ans=d.ai_answer;
      document.getElementById('ac').innerHTML=`<div class="badge">🤖 Gemini 2.0 Flash &nbsp;·&nbsp; 🌐 DuckDuckGo</div><div class="ans">${esc(d.ai_answer)}</div>`;
      document.getElementById('scb').disabled=false;
    }
    if(d.web_context&&d.web_context!=='No web results found.'){
      document.getElementById('ct').textContent=d.web_context;
      document.getElementById('cp').style.display='block';
    }
  }catch(e){
    document.getElementById('ti').classList.remove('on');
    document.getElementById('ac').innerHTML=`<div style="color:var(--danger);font-size:13px">Error: ${e.message}</div>`;
  }
  document.getElementById('sb').disabled=false;
}
async function doScore(){
  const ea=document.getElementById('ea').value.trim();
  if(!ea||!ans)return;
  sw('sc');
  document.getElementById('sph').innerHTML='<div style="padding:20px;font-size:12px;color:var(--muted)">⏳ Evaluating answers...</div>';
  document.getElementById('sph').style.display='block';
  document.getElementById('sd').classList.remove('on');
  try{
    const r=await fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:qry,ai_answer:ans,expected_answer:ea})});
    renderScore(await r.json());
  }catch(e){
    document.getElementById('sph').innerHTML=`<div style="color:var(--danger);font-size:13px">Error: ${e.message}</div>`;
  }
}
function renderScore(d){
  const s=d.total_score||0;
  document.getElementById('sph').style.display='none';
  document.getElementById('sd').classList.add('on');
  const c=s>=80?'#00d4aa':s>=60?'#7c6dff':s>=40?'#ffb347':'#ff4d6d';
  const f=document.getElementById('sf');
  f.style.stroke=c;
  setTimeout(()=>{f.style.strokeDashoffset=283-(s/100)*283;},50);
  animN('snum',0,s,1400);
  const vb=document.getElementById('vb');
  vb.textContent=d.verdict||'—';
  const vc={Excellent:'#00d4aa',Good:'#7c6dff',Acceptable:'#ffb347',Poor:'#ff4d6d'}[d.verdict]||'#7c6dff';
  vb.style.cssText=`background:${vc}20;border:1px solid ${vc}40;color:${vc};border-radius:20px;padding:6px 16px;`;
  const mb=document.getElementById('mb');
  mb.textContent=d.matches_expected?'✓ Matches expectation':'✗ Differs from expectation';
  mb.className='mb '+(d.matches_expected?'my':'mn');
  document.getElementById('sfb').textContent=d.feedback||'';
  const dims=[{l:'Factual Accuracy',k:'factual_accuracy',m:25},{l:'Completeness',k:'completeness',m:25},{l:'Relevance',k:'relevance',m:25},{l:'Clarity',k:'clarity',m:25}];
  document.getElementById('da').innerHTML=dims.map(x=>{
    const v=d[x.k]||0,p=(v/x.m)*100,bc=p>=80?'#00d4aa':p>=60?'#7c6dff':p>=40?'#ffb347':'#ff4d6d';
    return `<div class="dr"><div class="dl">${x.l}</div><div class="dbw"><div class="db" id="b-${x.k}" style="background:${bc}"></div></div><div class="ds">${v}/${x.m}</div></div>`;
  }).join('');
  setTimeout(()=>dims.forEach(x=>{const e=document.getElementById('b-'+x.k);if(e)e.style.width=((d[x.k]||0)/x.m*100)+'%';}),100);
}
function animN(id,s,e,dur){
  const el=document.getElementById(id),t0=performance.now();
  (function step(n){const t=Math.min((n-t0)/dur,1);el.textContent=Math.round(s+(e-s)*(1-Math.pow(1-t,3)));if(t<1)requestAnimationFrame(step);})(t0);
}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
document.getElementById('q').addEventListener('keydown',e=>{if(e.key==='Enter')doSearch();});
</script>
</body>
</html>"""


# ── THE HANDLER VERCEL ACTUALLY NEEDS ─────────────────────────────────────────
# Vercel's vc_init.py does: issubclass(handler, BaseHTTPRequestHandler)
# So 'handler' must be a CLASS that extends BaseHTTPRequestHandler.
# FastAPI / Flask / any WSGI-ASGI app object will fail this check.

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", ""):
            self._send(200, "text/html; charset=utf-8", HTML.encode())
        elif path == "/api/health":
            self._send_json({"status": "ok", "gemini_configured": bool(GEMINI_API_KEY)})
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._send_json({"error": "Invalid JSON body"}, status=400)
            return

        path = urlparse(self.path).path
        if path == "/api/search":
            self._send_json(handle_search(body))
        elif path == "/api/score":
            self._send_json(handle_score(body))
        else:
            self._send_json({"error": "Not found"}, status=404)

    def _send(self, status: int, content_type: str, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: dict, status: int = 200):
        self._send(status, "application/json", json.dumps(data).encode())

    def log_message(self, fmt, *args):
        pass  # Suppress default stdout logging in serverless