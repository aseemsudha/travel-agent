import streamlit as st

from core.llmops.analytics import (
    prompt_performance,
    hallucination_rate,
    tool_usage,
    success_rate,
    retry_rate,
    failure_reasons,
    prompt_stats
)

st.set_page_config(page_title="LLMOps Dashboard", layout="wide")

st.title("🚀 AI Agent Observability Dashboard")

# --- Top Metrics ---
col1, col2, col3 = st.columns(3)

col1.metric("✅ Success Rate", f"{success_rate()*100:.1f}%")
col2.metric("⚠️ Hallucination Rate", f"{hallucination_rate()*100:.1f}%")
col3.metric("🔁 Retry Rate", f"{retry_rate()*100:.1f}%")

st.divider()

# --- Prompt Performance ---
st.subheader("🧠 Prompt Performance (Relevance Score)")
st.write(prompt_performance())

# --- Prompt A/B Testing ---
st.subheader("⚖️ Prompt Success Comparison")
st.write(prompt_stats())

# --- Tool Usage ---
st.subheader("🛠️ Tool Usage")
st.bar_chart(tool_usage())

# --- Failures ---
st.subheader("⚠️ Failure Analysis")
st.write(failure_reasons())