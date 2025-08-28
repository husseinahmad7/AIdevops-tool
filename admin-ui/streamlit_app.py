import os
import requests
import streamlit as st

BASE = os.getenv("GATEWAY_BASE", "http://localhost:8080")
API = BASE + "/api/v1"

st.set_page_config(page_title="AIDevOps Admin", layout="wide")
st.title("AI DevOps Admin Console")

# Session state for token
if "token" not in st.session_state:
    st.session_state.token = ""


def req(path: str, method: str = "GET", json=None, params=None):
    try:
        headers = {}
        if st.session_state.token:
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        url = API + path if path.startswith("/") else path
        r = requests.request(
            method, url, headers=headers, json=json, params=params, timeout=10
        )
        return r
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


with st.sidebar:
    st.header("Auth")
    u = st.text_input("Username", value="demo")
    p = st.text_input("Password", value="demo123", type="password")
    if st.button("Login", key="login_btn"):
        try:
            r = requests.post(
                API + "/auth/login", data={"username": u, "password": p}, timeout=10
            )
            if r.ok:
                st.session_state.token = r.json().get("access_token", "")
                st.success("Logged in")
            else:
                st.error(f"Login failed: {r.status_code}")
        except Exception as e:
            st.error(f"Login error: {e}")
    manual = st.text_input("Paste JWT", value="")
    if st.button("Use token", key="use_token_btn") and manual:
        st.session_state.token = manual
        st.success("Token set")

col1, col2 = st.columns(2)

with col1:
    st.subheader("NLP")
    concept = st.text_input("Explain concept", value="devops")
    if st.button("Explain", key="nlp_explain"):
        r = req(f"/nlp/explain/{concept}")
        if r:
            st.code(r.text, language="json")
    q = st.text_area("Ask a question", value="What is CI/CD?")
    if st.button("Query", key="nlp_query"):
        r = req("/nlp/query", method="POST", json={"query": q, "use_context": False})
        if r:
            st.code(r.text, language="json")

    st.write("")
    st.caption("Optional: Time range and source for stats/anomalies")
    src = st.text_input("Log source (optional)", value="", key="logs_source")
    time_cols = st.columns(2)
    start_t = time_cols[0].text_input("Start ISO", value="", key="logs_start")
    end_t = time_cols[1].text_input("End ISO", value="", key="logs_end")
    if st.button("Statistics", key="logs_stats"):
        r = req(
            "/logs/statistics",
            params={
                "source": src or None,
                "start_time": start_t or None,
                "end_time": end_t or None,
            },
        )
        if r:
            st.code(r.text, language="json")
    if st.button("Anomalies", key="logs_anoms"):
        r = req(
            "/logs/anomalies",
            params={
                "source": src or None,
                "start_time": start_t or None,
                "end_time": end_t or None,
                "interval": "hour",
                "threshold": 2.0,
            },
        )
        if r:
            st.code(r.text, language="json")

    st.subheader("Logs")
    logs_q = st.text_input("Search logs", value="error")
    if st.button("Search Logs", key="logs_search"):
        r = req("/logs/search", params={"query": logs_q})
        if r:
            st.code(r.text, language="json")
    if st.button("Digest", key="logs_digest"):
        r = req(
            "/logs/digest",
            params={
                "source": src or None,
                "start_time": start_t or None,
                "end_time": end_t or None,
            },
        )
        if r:
            st.code(r.text, language="json")

    up = st.file_uploader("Upload .log/.txt", type=["log", "txt"])
    source = st.text_input("Log source", value="admin-ui")
    if st.button("Ingest Upload", key="logs_upload") and up:
        text = up.getvalue().decode("utf-8", errors="ignore")
        lines = [l for l in text.splitlines() if l][:200]
        payload = {
            "source": source,
            "logs": [{"timestamp": "", "level": "INFO", "message": l} for l in lines],
        }
        r = req("/logs/ingest", method="POST", json=payload)
        if r:
            st.code(r.text, language="json")

with col2:
    st.caption("CI/CD Tables")
    if st.button("Pipelines (table)", key="cicd_pipelines_tbl"):
        r = req("/cicd/pipelines?token=" + st.session_state.token)
        if r and r.ok:
            try:
                st.dataframe(r.json().get("pipelines", []))
            except Exception:
                st.code(r.text, language="json")
    if st.button("Metrics (table)", key="cicd_metrics_tbl"):
        r = req("/cicd/metrics?token=" + st.session_state.token)
        if r and r.ok:
            try:
                st.dataframe(r.json().get("metrics", {}), use_container_width=True)
            except Exception:
                st.code(r.text, language="json")

    st.subheader("CI/CD")
    if st.button("Pipelines", key="cicd_pipelines"):
        r = req("/cicd/pipelines?token=" + st.session_state.token)
        if r:
            st.code(r.text, language="json")
    if st.button("Metrics", key="cicd_metrics"):
        r = req("/cicd/metrics?token=" + st.session_state.token)
        if r:
            st.code(r.text, language="json")
    pipeline_id = st.text_input("Pipeline ID", value="main")
    if st.button("Analyze Pipeline", key="cicd_analyze"):
        r = req(
            f"/cicd/pipelines/{pipeline_id}/analysis?token=" + st.session_state.token
        )
        if r:
            st.code(r.text, language="json")

    st.subheader("Resources")
    c1, c2, c3 = st.columns(3)
    if c1.button("Usage", key="res_usage"):
        r = req("/resources/usage")
        if r:
            st.code(r.text, language="json")
    if c2.button("Costs", key="res_costs"):
        r = req("/resources/costs")
        if r:
            st.code(r.text, language="json")
    if c3.button("Metrics", key="res_metrics"):
        r = req("/resources/metrics")
        if r:
            st.code(r.text, language="json")
    if st.button("Optimize", key="res_optimize"):
        r = req(
            "/resources/optimize", method="POST", json={"targets": ["cpu", "storage"]}
        )
        if r:
            st.code(r.text, language="json")

st.subheader("Notifications")
email = st.text_input("Recipient", value="admin@example.com")
lmsg = st.text_input("Message", value="Hello")
if st.button("Send Notification", key="notif_send"):
    r = req(
        "/notifications/send",
        method="POST",
        json={"channels": ["email"], "message": lmsg, "recipients": [email]},
    )
    if r:
        st.code(r.text, language="json")

st.subheader("Reporting")
cols = st.columns(2)
if cols[0].button("Templates", key="rep_templates"):
    r = req("/reports/templates")
    if r:
        st.code(r.text, language="json")
st.subheader("AI Prediction")
colp1, colp2, colp3, colp4 = st.columns(4)
if colp1.button("Forecast (tiny)", key="pred_forecast_btn2"):
    series = [{"ds": f"2024-01-0{i+1}", "y": i} for i in range(7)]
    r = req(
        "/predictions/forecast",
        method="POST",
        json={"data": series, "metric_name": "demo", "days": 1},
    )
    if r:
        st.code(r.text, language="json")

colp5, colp6 = st.columns(2)
if colp5.button("Train Model", key="pred_train_btn"):
    dataset = [{"ds": f"2024-01-0{i+1}", "y": i} for i in range(14)]
    r = req(
        "/predictions/train",
        method="POST",
        json={"data": dataset, "model_name": "prophet"},
    )
    if r:
        st.code(r.text, language="json")
if colp6.button("Batch Predict", key="pred_batch_btn"):
    batch = {
        "predictions": [
            {
                "type": "forecast",
                "data": {
                    "data": [{"ds": f"2024-01-0{i+1}", "y": i} for i in range(7)],
                    "metric_name": "demo",
                    "days": 1,
                },
            },
            {
                "type": "anomalies",
                "data": {
                    "data": [{"ds": f"2024-01-0{i+1}", "y": i} for i in range(7)],
                    "metric_name": "demo",
                    "threshold": 2.0,
                },
            },
        ]
    }
    r = req("/predictions/batch", method="POST", json=batch)
    if r:
        st.code(r.text, language="json")

    series = [{"ds": f"2024-01-0{i+1}", "y": i} for i in range(7)]
    r = req(
        "/predictions/forecast",
        method="POST",
        json={"data": series, "metric_name": "demo", "days": 1},
    )
    if r:
        st.code(r.text, language="json")
if colp2.button("Anomalies", key="pred_anomalies_btn"):
    series = [{"ds": f"2024-01-0{i+1}", "y": i} for i in range(7)]
    r = req(
        "/predictions/anomalies",
        method="POST",
        json={"data": series, "metric_name": "demo", "threshold": 2.0},
    )
    if r:
        st.code(r.text, language="json")
if colp3.button("Predict Resources", key="pred_resources_btn"):
    hist = [{"t": i, "cpu": i % 5} for i in range(24)]
    r = req(
        "/predictions/resources/predict",
        method="POST",
        json={"data": hist, "resource_type": "cpu", "hours": 24},
    )
    if r:
        st.code(r.text, language="json")
if colp4.button("Predict Incidents", key="pred_incidents_btn"):
    hist = [{"ts": i, "sev": i % 3} for i in range(10)]
    metrics = [{"ts": i, "cpu": (i % 5) * 10} for i in range(10)]
    r = req(
        "/predictions/incidents/predict",
        method="POST",
        json={"historical_incidents": hist, "system_metrics": metrics},
    )
    if r:
        st.code(r.text, language="json")


if cols[1].button("Generate Report", key="rep_generate"):
    r = req(
        "/reports/generate",
        method="POST",
        json={"template_id": "demo", "parameters": {}, "format": "json"},
    )
    if r:
        st.code(r.text, language="json")


st.subheader("Elasticsearch")
cols_es = st.columns(2)
if cols_es[0].button("Cluster Health", key="es_health"):
    r = req("/logs/admin/elastic/health")
    if r and r.ok:
        st.json(r.json())
    else:
        st.error(f"Health error: {r.status_code if r else 'no response'}")
if cols_es[1].button("List Indices", key="es_indices"):
    r = req("/logs/admin/elastic/indices")
    if r and r.ok:
        try:
            st.dataframe(r.json().get("indices", []), use_container_width=True)
        except Exception:
            st.code(r.text, language="json")

st.subheader("Health via Gateway")
cells = st.columns(5)
services = [
    "users",
    "nlp",
    "logs",
    "predictions",
    "monitoring",
    "cicd",
    "resources",
    "notifications",
    "reports",
]
for i, svc in enumerate(services):
    if cells[i % 5].button(f"{svc}", key=f"health_{svc}"):
        r = req(f"/{svc}/health")
        if r:
            st.code(r.text, language="json")

st.caption(
    "Set GATEWAY_BASE env var to target a different gateway host (default http://localhost:8080)"
)
