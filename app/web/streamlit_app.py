from __future__ import annotations

import os

import httpx
import streamlit as st

API_URL = os.getenv("UI_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Crypto Agent Research", layout="wide")
st.title("Crypto Agent Research")
st.caption(
    "Five-agent (Scout / Analyst / Trader / Risk / Reflector) research loop on Binance public data. "
    "Paper-only — no orders are placed. See README for compliance notes."
)


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_URL, timeout=300.0)


with st.sidebar:
    st.header("Run a cycle")
    reflect = st.checkbox(
        "Run Reflector at the end",
        value=False,
        help="Reflector is expensive; run every Nth cycle in practice.",
    )
    if st.button("Run cycle", type="primary"):
        with st.spinner("Agents working..."):
            with _client() as c:
                resp = c.post("/api/cycles/run", json={"reflect": reflect})
                resp.raise_for_status()
                st.session_state["last_report"] = resp.json()
        st.success("Cycle complete.")

    st.divider()
    st.subheader("Memory")
    refresh = st.button("Refresh memory views")

if "last_report" in st.session_state:
    report = st.session_state["last_report"]

    st.subheader(f"Cycle {report['cycle_id']}")
    cols = st.columns(3)
    cols[0].metric("Candidates", len(report["candidates"]))
    cols[1].metric("Decision", (report["decision"] or {}).get("action", "—"))
    cols[2].metric(
        "Total tokens (in+out)",
        sum(report["total_usage"].get(k, 0) for k in ("input_tokens", "output_tokens")),
    )

    if report["candidates"]:
        st.write("**Candidates:** " + ", ".join(report["candidates"]))

    st.subheader("Decision")
    st.json(report["decision"] or {"action": "no decision"})
    if report["risk_verdict"]:
        st.write("**Risk verdict:**")
        st.json(report["risk_verdict"])
    if report.get("lesson"):
        st.write("**Recorded lesson:**")
        st.json(report["lesson"])

    st.subheader("Agent traces")
    for run in report["agent_runs"]:
        title = f"{run['role']} ({run['model']}) — {run['turns']} turns, {run['stop_reason']}"
        with st.expander(title):
            st.write("**Token usage:**")
            st.json(run["usage"])
            if run["final_text"]:
                st.write("**Final text:**")
                st.code(run["final_text"])
            if run["tool_log"]:
                st.write("**Tool calls:**")
                for entry in run["tool_log"]:
                    st.markdown(f"- `{entry['tool']}({entry['args']})`")
                    st.caption(str(entry["result"])[:500])

st.divider()
st.subheader("Persistent memory")
if refresh or st.session_state.get("memory_loaded") is None:
    with _client() as c:
        st.session_state["decisions"] = c.get("/api/decisions", params={"limit": 20}).json()
        st.session_state["lessons"] = c.get("/api/lessons").json()
        st.session_state["outcomes"] = c.get("/api/outcomes", params={"limit": 20}).json()
        st.session_state["memory_loaded"] = True

mem_cols = st.columns(3)
with mem_cols[0]:
    st.write(f"**Lessons** ({st.session_state.get('lessons', {}).get('count', 0)})")
    for lesson in (st.session_state.get("lessons") or {}).get("items", []):
        st.markdown(f"- {lesson.get('text', '')}")
        st.caption(lesson.get("ts", ""))
with mem_cols[1]:
    st.write(f"**Recent decisions** ({st.session_state.get('decisions', {}).get('count', 0)})")
    for dec in (st.session_state.get("decisions") or {}).get("items", []):
        st.markdown(f"- **{dec.get('action')}** {dec.get('symbol')} @ {dec.get('size_pct')}%")
        st.caption((dec.get("reasoning") or "")[:160])
with mem_cols[2]:
    st.write(f"**Recent outcomes** ({st.session_state.get('outcomes', {}).get('count', 0)})")
    for outcome in (st.session_state.get("outcomes") or {}).get("items", []):
        st.json(outcome)
