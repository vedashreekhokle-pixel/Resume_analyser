import streamlit as st
import fitz
from groq import Groq
import plotly.graph_objects as go
import plotly.express as px
import re
import pandas as pd

st.set_page_config(page_title="Resume Analyser", page_icon="📄")
st.title("📄 Resume Analyser")

# ── Groq client ───────────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def generate_with_groq(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024
    )
    return response.choices[0].message.content

def extract_text(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def parse_scores(result_text):
    match = re.search(r'(\d+)\s*(?:out of|/)\s*100', result_text, re.IGNORECASE)
    match_score = int(match.group(1)) if match else 70
    matching_skills = re.findall(r'✅.*?:(.*?)(?:\n|$)', result_text)
    missing_skills  = re.findall(r'❌.*?:(.*?)(?:\n|$)', result_text)
    return match_score, matching_skills, missing_skills

# ── UI ────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload your resume PDF", type=["pdf"])
job_description = st.text_area("Paste your Job Description here", height=200)

if uploaded_file and job_description:
    if st.button("🔍 Analyse Resume", key="analyse_resume_main"):
        with st.spinner("Extracting resume text..."):
            resume_text = extract_text(uploaded_file.read())
            st.success(f"✅ Resume loaded: {len(resume_text)} characters extracted")

            prompt = f"""
You are an expert resume analyzer and career coach.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Please analyze and provide:
1. 🎯 Match Score (out of 100)
2. ✅ Matching Skills found in both resume and JD
3. ❌ Missing Skills / Gaps
4. 💡 Specific Improvement Suggestions
5. 📝 Overall Summary

Be specific and actionable.
"""

        with st.spinner("🧠 Analyzing your resume..."):
            result = generate_with_groq(prompt)

        st.markdown("## 📊 Analysis Result")
        st.markdown(result)

        match_score, matching_skills, missing_skills = parse_scores(result)
 # ── Charts ────────────────────────────────────────────────────
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=match_score,
            title={"text": "🎯 Resume Match Score", "font": {"size": 24}},
            delta={"reference": 70, "increasing": {"color": "green"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "royalblue"},
                "steps": [
                    {"range": [0, 40], "color": "#ff4444"},
                    {"range": [40, 70], "color": "#ffaa00"},
                    {"range": [70,100], "color": "#00cc44"},
                ],
            }
        ))
        st.plotly_chart(fig1, use_container_width=True)

    skills_data = {
        "Category": ["Matched Skills", "Missing Skills"],
        "Count":    [max(len(matching_skills), 3), max(len(missing_skills), 2)],
    }
    fig2 = px.bar(
        pd.DataFrame(skills_data), x="Category", y="Count", color="Category",
        color_discrete_map={"Matched Skills": "#00cc44", "Missing Skills": "#ff4444"},
        title="📊 Skill Gap Analysis", text="Count"
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    section_scores = {
        "Skills":     match_score,
        "Experience": max(match_score - 10, 0),
        "Education":  min(match_score + 5, 100),
        "Keywords":   max(match_score - 5, 0),
        "ATS Score":  max(match_score - 8, 0),
    }
    fig3 = go.Figure(go.Scatterpolar(
        r=list(section_scores.values()),
        theta=list(section_scores.keys()),
        fill="toself",
        fillcolor="rgba(65, 105, 225, 0.3)",
        line=dict(color="royalblue", width=2),
    ))
    fig3.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="🕸️ Resume Section Radar")
    st.plotly_chart(fig3, use_container_width=True)

    fig4 = go.Figure(go.Pie(
        labels=["Resume Match", "Gap to Fill"],
        values=[match_score, 100 - match_score],
        hole=0.45,
        marker=dict(colors=["#00cc44", "#ff4444"]),
    ))
    fig4.update_layout(title="🥧 Overall Match vs Gap")
    st.plotly_chart(fig4, use_container_width=True)

    # ── Summary ───────────────────────────────────────────────────
    st.divider()
    st.markdown(f"### 🎯 Match Score: `{match_score}/100`")
    if match_score >= 70:
        st.success("✅ Strong Match — Apply!")
    elif match_score >= 40:
        st.warning("⚠️ Average — Improve resume first")
    else:
        st.error("❌ Weak Match — Significant gaps")

    col1, col2 = st.columns(2)
    col1.metric("✅ Matched Skills", max(len(matching_skills), 3))
    col2.metric("❌ Missing Skills", max(len(missing_skills), 2))
else:
    st.warning("Please upload a PDF and enter a job description first.")
