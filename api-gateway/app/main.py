from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
import httpx
import os
from .config import settings
from .auth import get_current_user
from .routes import router as api_router

app = FastAPI(
    title="AI DevOps Assistant API Gateway",
    description="API Gateway for the AI DevOps Assistant microservices",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to AI DevOps Assistant API Gateway"}

# Prometheus-style scrape endpoint (stub) to avoid 404s
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_stub():
    return "# HELP gateway_up 1 if the gateway is up\n# TYPE gateway_up gauge\ngateway_up 1\n"


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail":exc.detail})


# Simple Admin Test UI
@app.get("/admin", response_class=HTMLResponse)
async def admin_ui():
    return """
<!doctype html>
<html>
<head>
  <meta charset='utf-8'/>
  <title>AI DevOps Admin Test UI</title>
  <script src="https://unpkg.com/htmx.org@1.9.12"></script>
  <style>
    body{font-family:sans-serif;margin:24px;}
    section{margin-bottom:24px;}
    textarea{width:100%;height:80px;}
    code{background:#f4f4f4;padding:2px 4px;}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;}
    .card{border:1px solid #ddd;border-radius:8px;padding:12px;}
    .row{display:flex;gap:8px;align-items:center;}
  </style>
</head>
<body>
  <h1>AI DevOps Admin Test UI</h1>
  <p>Use this page to perform authenticated tests through the API Gateway. Token is stored in-memory only.</p>

  <!-- 1) Login & token picker -->
  <section class="card">
    <h2>1) Login to get JWT</h2>
    <form id="loginForm">
      <div class="row">
        <label>Username <input id="u" value="demo"/></label>
        <label>Password <input id="p" type="password" value="demo123"/></label>
        <button>Login</button>
      </div>
    </form>
    <div class="row" style="margin-top:8px">
      <label>Manual token <input id="manualToken" placeholder="paste JWT here" style="min-width:360px"/></label>
      <button id="useTokenBtn" type="button">Use token</button>
    </div>
    <p>Token: <code id="token"></code></p>
  </section>


  <!-- 2) Users -->
  <section class="card">
    <h2>Users</h2>
    <div class="row">
      <button id="validateBtn">GET /api/v1/users/validate</button>
    </div>
    <pre id="validateOut"></pre>
  </section>

  <!-- 3) NLP -->
  <section class="card">
    <h2>NLP</h2>
    <div class="row">
      <input id="concept" value="devops"/>
      <button id="explainBtn">GET /api/v1/nlp/explain/{concept}</button>
    </div>
    <div class="row">
      <textarea id="query">What is CI/CD?</textarea>
      <button id="queryBtn">POST /api/v1/nlp/query</button>
    </div>
    <pre id="explainOut"></pre>
    <pre id="queryOut"></pre>
  </section>

  <!-- 4) Logs -->
  <section class="card">
    <h2>Logs</h2>
    <div class="row">
      <input id="logsQ" value="error"/>
      <button id="logsBtn">GET /api/v1/logs/search</button>
    </div>
    <div class="row">
      <input id="logsSource" placeholder="source name"/>
      <input id="logsFile" type="file" accept=".log,.txt"/>
      <button id="logsUploadBtn">POST /api/v1/logs/ingest (upload)</button>
    </div>
    <small>Upload reads the file, splits lines, and ingests the first 200 lines as logs.</small>
    <pre id="logsOut"></pre>
  </section>

  <!-- 5) CI/CD -->
  <section class="card">
    <h2>CI/CD</h2>
    <div class="row">
      <button id="cicdPipelinesBtn">GET /api/v1/cicd/pipelines</button>
      <button id="cicdMetricsBtn">GET /api/v1/cicd/metrics</button>
    </div>
    <div class="row">
      <input id="pipelineId" value="main"/> <button id="cicdAnalysisBtn">GET /api/v1/cicd/pipelines/{id}/analysis</button>
    </div>
    <pre id="cicdOut"></pre>
  </section>

  <!-- 6) Resources -->
  <section class="card">
    <h2>Resources</h2>
    <div class="row">
      <button id="resUsageBtn">GET /api/v1/resources/usage</button>
      <button id="resCostsBtn">GET /api/v1/resources/costs</button>
      <button id="resMetricsBtn">GET /api/v1/resources/metrics</button>
    </div>
    <div class="row">
      <button id="resOptimizeBtn">POST /api/v1/resources/optimize</button>
    </div>
    <pre id="resOut"></pre>
  </section>

  <!-- 7) Notifications -->
  <section class="card">
    <h2>Notifications</h2>
    <div class="row">
      <button id="notifTemplatesBtn">GET /api/v1/notifications/templates</button>
    </div>
    <div class="row">
      <input id="notifTo" value="admin@example.com" style="min-width:220px"/>
      <button id="notifSendBtn">POST /api/v1/notifications/send</button>
  <!-- 8.5) Predictions -->
  <section class="card">
    <h2>Predictions</h2>
    <div class="row">
      <button id="predForecastBtn">POST /api/v1/predictions/forecast (tiny)</button>
    </div>
    <pre id="predOut"></pre>
  </section>

  <!-- 8.6) Infrastructure Metrics -->
  <section class="card">
    <h2>Infrastructure</h2>
    <div class="row">
      <button id="infraMetricsBtn">GET /api/v1/monitoring/metrics</button>
    </div>
    <pre id="infraOut"></pre>
  </section>

    </div>
    <pre id="notifOut"></pre>
  </section>

  <!-- 8) Reporting -->
  <section class="card">
    <h2>Reporting</h2>
    <div class="row">
      <button id="repTemplatesBtn">GET /api/v1/reports/templates</button>
      <button id="repGenerateBtn">POST /api/v1/reports/generate</button>
    </div>
    <pre id="repOut"></pre>
  </section>

  <!-- 9) Health via Gateway -->
  <section class="card">
    <h2>Service Health (via Gateway)</h2>
    <div class="grid">
      <button data-health="/api/v1/users/health">users</button>
      <button data-health="/api/v1/nlp/health">nlp</button>
      <button data-health="/api/v1/logs/health">logs</button>
      <button data-health="/api/v1/predictions/health">predictions</button>
      <button data-health="/api/v1/monitoring/health">monitoring</button>
      <button data-health="/api/v1/cicd/health">cicd</button>
      <button data-health="/api/v1/resources/health">resources</button>
      <button data-health="/api/v1/notifications/health">notifications</button>
      <button data-health="/api/v1/reports/health">reports</button>
    </div>
    <pre id="healthOut"></pre>
  </section>

  <script>
  let token="";
  async function req(path, opts={}){
    opts.headers = opts.headers || {};
    if(token) opts.headers['Authorization'] = 'Bearer '+token;
    const r = await fetch(path, opts);
    const t = await r.text();
    try{ return {status:r.status, json: JSON.parse(t)} }catch(_){ return {status:r.status, text:t} }
  }
  document.getElementById('loginForm').addEventListener('submit', async (e)=>{
    e.preventDefault();
    const u = document.getElementById('u').value;
    const p = document.getElementById('p').value;
    const bodyData = 'username=' + encodeURIComponent(u) + '&password=' + encodeURIComponent(p);
    const r = await fetch('/api/v1/auth/login', {
      method: "POST",
      headers: {"Content-Type": "application/x-www-form-urlencoded"},
      body: bodyData
    });
    const js = await r.json();
    token = js.access_token || '';
    document.getElementById('token').innerText = token ? (token.slice(0,24)+'...') : '(none)';
  });
  document.getElementById('validateBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/users/validate');
    document.getElementById('validateOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('explainBtn').addEventListener('click', async ()=>{
    const concept = document.getElementById('concept').value;
    const r = await req('/api/v1/nlp/explain/'+encodeURIComponent(concept));
    document.getElementById('explainOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('queryBtn').addEventListener('click', async ()=>{
    const q = document.getElementById('query').value;
    const r = await req('/api/v1/nlp/query', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query:q, use_context:false})});
    document.getElementById('queryOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('logsBtn').addEventListener('click', async ()=>{
    const q = document.getElementById('logsQ').value;
    const r = await req('/api/v1/logs/search?query='+encodeURIComponent(q));
    document.getElementById('logsOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('cicdPipelinesBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/cicd/pipelines?token='+encodeURIComponent(token));
    document.getElementById('cicdOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('cicdMetricsBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/cicd/metrics?token='+encodeURIComponent(token));
    document.getElementById('cicdOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('cicdAnalysisBtn').addEventListener('click', async ()=>{
    const id = document.getElementById('pipelineId').value;
    const r = await req('/api/v1/cicd/pipelines/'+encodeURIComponent(id)+'/analysis?token='+encodeURIComponent(token));
    document.getElementById('cicdOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('resUsageBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/resources/usage');
    document.getElementById('resOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('resCostsBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/resources/costs');
    document.getElementById('resOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('resMetricsBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/resources/metrics');
    document.getElementById('resOut').innerText = JSON.stringify(r.json||r.text, null, 2);

  document.getElementById('predForecastBtn').addEventListener('click', async ()=>{
    const series = Array.from({length:7}).map((_,i)=>({ds:'2024-01-0'+(i+1), y:i}));
    const r = await req('/api/v1/predictions/forecast', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({data: series, metric_name:'demo', days:1})});
    document.getElementById('predOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('infraMetricsBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/monitoring/metrics');
    document.getElementById('infraOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('logsUploadBtn').addEventListener('click', async ()=>{
    const f = document.getElementById('logsFile').files[0];
    const source = document.getElementById('logsSource').value || 'admin-ui';
    if(!f){ alert('Choose a file'); return; }
    const text = await f.text();
    const lines = text.split(/\\r?\\n/).filter(Boolean).slice(0,200);
    const payload = { source, logs: lines.map(l=>({ timestamp: new Date().toISOString(), level: 'INFO', message: l })) };
    const r = await req('/api/v1/logs/ingest', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    document.getElementById('logsOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });

    const text = await f.text();
    const lines = text.split(/\\r?\\n/).filter(Boolean).slice(0,200);
    const payload = { source, logs: lines.map(l=>({ timestamp: new Date().toISOString(), level: 'INFO', message: l })) };
    const r = await req('/api/v1/logs/ingest', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    document.getElementById('logsOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('resOptimizeBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/resources/optimize', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({targets:["cpu","storage"]})});
    document.getElementById('resOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('notifTemplatesBtn').addEventListener('click', async ()=>{
    const r = await req('/api/v1/notifications/templates');
    document.getElementById('notifOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.getElementById('notifSendBtn').addEventListener('click', async ()=>{
    const to = document.getElementById('notifTo').value;
    const r = await req('/api/v1/notifications/send', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({channels:["email"], message:"Hello", recipients:[to]})});
    document.getElementById('notifOut').innerText = JSON.stringify(r.json||r.text, null, 2);
  });
  document.querySelectorAll('[data-health]').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      const url = btn.getAttribute('data-health');
      const r = await req(url);

      const prev = document.getElementById('healthOut').innerText;
      document.getElementById('healthOut').innerText = (prev? prev+"\n":"") + url+': '+JSON.stringify(r.json||r.text);
    });
  });
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)