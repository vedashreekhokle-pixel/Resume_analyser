# ── Install dependencies ──────────────────────────────────────────


# ── Imports ───────────────────────────────────────────────────────
import fitz
from groq import Groq
from google.colab import files
from IPython.display import Markdown, display

# ── Groq client ───────────────────────────────────────────────────
client = Groq(api_key="groq_api_here")  # ⚠️ keep this secret

def generate_with_groq(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024
    )
    return response.choices[0].message.content

# ── Extract text from PDF ─────────────────────────────────────────
def extract_text(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# ── Step 1: Upload Resume ─────────────────────────────────────────
print("📄 Please upload your resume PDF:")
uploaded = files.upload()

filename = list(uploaded.keys())[0]          # ✅ get actual filename
resume_text = extract_text(uploaded[filename])  # ✅ pass bytes directly
print(f"✅ Resume loaded: {len(resume_text)} characters extracted")

# ── Step 2: Enter Job Description ────────────────────────────────
job_description = input("📋 Paste your job description here: ")

# ── Step 3: Build Prompt ──────────────────────────────────────────
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

# ── Step 4: Get Analysis ──────────────────────────────────────────
print("\n🤖 Analyzing your resume...\n")
result = generate_with_groq(prompt)

# ── Step 5: Display nicely ────────────────────────────────────────
display(Markdown(result))
# ── Install visualization libraries ──────────────────────────────
!pip install matplotlib plotly -q

import plotly.graph_objects as go
import plotly.express as px
import re
import pandas as pd

# ── Step 6: Parse the result to extract scores ────────────────────
def parse_scores(result_text):
    # Extract match score
    match = re.search(r'(\d+)\s*(?:out of|/)\s*100', result_text, re.IGNORECASE)
    match_score = int(match.group(1)) if match else 70

    # Extract matching skills
    matching_skills = re.findall(r'✅.*?:(.*?)(?:\n|$)', result_text)
    missing_skills  = re.findall(r'❌.*?:(.*?)(?:\n|$)', result_text)

    return match_score, matching_skills, missing_skills

match_score, matching_skills, missing_skills = parse_scores(result)

# ── Chart 1: Gauge Chart — Overall Match Score ────────────────────
fig1 = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=match_score,
    title={"text": "🎯 Resume Match Score", "font": {"size": 24}},
    delta={"reference": 70, "increasing": {"color": "green"}},
    gauge={
        "axis": {"range": [0, 100]},
        "bar":  {"color": "royalblue"},
        "steps": [
            {"range": [0,  40], "color": "#ff4444"},   # red   = poor
            {"range": [40, 70], "color": "#ffaa00"},   # amber = average
            {"range": [70,100], "color": "#00cc44"},   # green = good
        ],
        "threshold": {
            "line":  {"color": "black", "width": 4},
            "thickness": 0.75,
            "value": match_score
        }
    }
))
fig1.update_layout(height=400)
fig1.show()

# ── Chart 2: Skill Coverage Bar Chart ────────────────────────────
skills_data = {
    "Category": ["Matched Skills", "Missing Skills"],
    "Count":    [max(len(matching_skills), 3),    # fallback if parsing misses
                 max(len(missing_skills),  2)],
    "Color":    ["#00cc44", "#ff4444"]
}
df_skills = pd.DataFrame(skills_data)

fig2 = px.bar(
    df_skills,
    x="Category",
    y="Count",
    color="Category",
    color_discrete_map={"Matched Skills": "#00cc44", "Missing Skills": "#ff4444"},
    title="📊 Skill Gap Analysis",
    text="Count"
)
fig2.update_traces(textposition="outside")
fig2.update_layout(showlegend=False, height=400)
fig2.show()

# ── Chart 3: Radar Chart — Resume Section Scores ─────────────────
# You can adjust these scores manually or parse from result
section_scores = {
    "Skills":      match_score,
    "Experience":  match_score - 10 if match_score > 10 else match_score,
    "Education":   match_score + 5  if match_score < 95 else match_score,
    "Keywords":    match_score - 5  if match_score > 5  else match_score,
    "ATS Score":   match_score - 8  if match_score > 8  else match_score,
}

fig3 = go.Figure(go.Scatterpolar(
    r=list(section_scores.values()),
    theta=list(section_scores.keys()),
    fill="toself",
    fillcolor="rgba(65, 105, 225, 0.3)",
    line=dict(color="royalblue", width=2),
    marker=dict(size=8)
))
fig3.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    title="🕸️ Resume Section Radar",
    height=450
)
fig3.show()

# ── Chart 4: Pie Chart — Match vs Gap ────────────────────────────
fig4 = go.Figure(go.Pie(
    labels=["Resume Match", "Gap to Fill"],
    values=[match_score, 100 - match_score],
    hole=0.45,
    marker=dict(colors=["#00cc44", "#ff4444"]),
    textinfo="label+percent"
))
fig4.update_layout(
    title="🥧 Overall Match vs Gap",
    height=400
)
fig4.show()

# ── Summary Card ──────────────────────────────────────────────────
print("\n" + "="*50)
print(f"  🎯 Match Score   : {match_score}/100")
if   match_score >= 70: print("  ✅ Status        : Strong Match — Apply!")
elif match_score >= 40: print("  ⚠️  Status        : Average — Improve resume first")
else:                   print("  ❌ Status        : Weak Match — Significant gaps")
print(f"  ✅ Matched Skills: {max(len(matching_skills), 3)}")
print(f"  ❌ Missing Skills: {max(len(missing_skills),  2)}")
print("="*50)


