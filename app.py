תשמור לי את הקוד הזה: import os
import subprocess
import sys

# 1. התקנה אוטומטית של סביבת העבודה (מיועד ל-Codespace)
def install_requirements():
    packages = ['PyPDF2', 'google-generativeai', 'pdf2image', 'PyMuPDF', 'pillow', 'plotly']
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io

# ==========================================
# 2. SETUP & SECURE AI
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
except Exception:
    st.error("❌ מפתח API לא נמצא ב-Secrets! המערכת מושבתת.")
    st.stop()

@st.cache_resource
def get_stable_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priorities = ['models/gemini-1.5-pro', 'models/gemini-1.5-flash']
        for p in priorities:
            if p in available_models:
                return genai.GenerativeModel(p), p
        return genai.GenerativeModel(available_models[0]), available_models[0]
    except Exception as e:
        return None, str(e)

ai_model, active_model_name = get_stable_model()

# ==========================================
# 3. VERIFIED DATA WAREHOUSE LOGIC
# ==========================================
BASE_WAREHOUSE = "data/Insurance_Warehouse"

def get_verified_paths(company, year, quarter):
    base = os.path.join(BASE_WAREHOUSE, company, str(year), quarter)
    fin_dir = os.path.join(base, "Financial_Reports")
    sol_dir = os.path.join(base, "Solvency_Reports")
    fin_files = [os.path.join(fin_dir, f) for f in os.listdir(fin_dir) if f.endswith('.pdf')] if os.path.exists(fin_dir) else []
    sol_files = [os.path.join(sol_dir, f) for f in os.listdir(sol_dir) if f.endswith('.pdf')] if os.path.exists(sol_dir) else []
    return fin_files, sol_files

# נתוני שוק מלאים (ה-KPI Checklist שלך)
market_df = pd.DataFrame({
    "חברה": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "Solvency %": [184, 172, 175, 158, 149],
    "ROE %": [14.1, 11.8, 12.5, 10.2, 10.4],
    "CSM (B₪)": [14.8, 14.1, 9.7, 11.2, 11.5],
    "Combined Ratio %": [91.5, 93.2, 92.8, 95.1, 94.4],
    "Expense Ratio %": [18.2, 19.1, 17.5, 20.4, 19.8],
    "NB Margin %": [4.8, 4.5, 4.3, 3.8, 3.9]
})

# ==========================================
# 4. SIDEBAR - PATH VALIDATOR & CONTROL
# ==========================================
with st.sidebar:
    st.header("🛡️ Path Validator")
    sel_comp = st.selectbox("בחר חברה לניתוח:", market_df["חברה"])
    sel_year = st.selectbox("שנה פיסקאלית:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון דיווח:", options=["Q1", "Q2", "Q3", "Q4"])
    
    fin_paths, sol_paths = get_verified_paths(sel_comp, sel_year, sel_q)
    
    st.divider()
    st.subheader("📁 Database Radar")
    if fin_paths: st.success(f"✅ דוח כספי: {os.path.basename(fin_paths[0])[:20]}...")
    else: st.warning("❌ דוח כספי חסר בנתיב")
    
    if sol_paths: st.success(f"✅ דוח סולבנסי: {os.path.basename(sol_paths[0])[:20]}...")
    else: st.warning("❌ דוח סולבנסי חסר בנתיב")
    
    st.caption(f"AI: {active_model_name}")

# ==========================================
# 5. MAIN TERMINAL (ALL TABS RESTORED)
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 Critical KPIs", "⛓️ IFRS 17 Engine", "📈 Financial Ratios", "🛡️ Stress Scenarios", "🤖 AI Deep Research"])

# --- TAB 1: 5 Critical KPIs ---
with tabs[0]:
    row = market_df[market_df["חברה"] == sel_comp].iloc[0]
    st.subheader("מדדי ליבה - IFRS 17 & Solvency II")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Solvency Ratio", f"{row['Solvency %']}%")
    k2.metric("ROE", f"{row['ROE %']}%")
    k3.metric("Combined Ratio", f"{row['Combined Ratio %']}%")
    k4.metric("CSM Balance", f"₪{row['CSM (B₪)']}B")
    k5.metric("Exp. Ratio", f"{row['Expense Ratio %']}%")
    
    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(px.bar(market_df, x="חברה", y="CSM (B₪)", color="חברה", title="השוואת עתודות רווח (CSM)"), use_container_width=True)
    with col_g2:
        st.plotly_chart(px.pie(values=[60, 25, 15], names=["Life", "Health", "P&C"], title="Profit Mix by Segment"), use_container_width=True)

# --- TAB 2: IFRS 17 ENGINE (CSM & ONEROUS) ---
with tabs[1]:
    st.subheader("⛓️ IFRS 17: CSM Analytics & Onerous Contracts")
    
    # 1. מיפוי מודלים
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.info("**VFA Approach**\n\nחיסכון ארוך טווח, ביטוח מנהלים")
    m_col2.success("**GMM Approach**\n\nריסק, סיעוד, חיים מסורתי")
    m_col3.warning("**PAA Approach**\n\nאלמנטר ובריאות קצר מועד")
    
    st.divider()
    
    # 2. חוזים מכבידים ומרכיב הפסד
    st.write("### 🌋 חוזים מכבידים (Onerous Contracts)")
    lc_col1, lc_col2 = st.columns([2, 1])
    with lc_col1:
        # גרף מפל CSM
        fig_wf = go.Figure(go.Waterfall(
            x = ["יתרת פתיחה", "חוזים חדשים", "חוזים מכבידים", "ריבית/אומדן", "שחרור לרווח", "יתרת סגירה"],
            y = [14200, 850, -320, 210, -1100, 13840],
            measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
        ))
        st.plotly_chart(fig_wf, use_container_width=True)
    with lc_col2:
        st.error("**Loss Component (LC)**")
        st.write("כאשר קבוצת חוזים הופכת למכבידה, נוצר מרכיב הפסד המוכר מיד בדו''ח רווח והפסד.")
        st.metric("Estimated LC Impact", "-₪320M")

# --- TAB 3: FINANCIAL RATIOS (WITH PROFESSIONAL EXPLANATIONS) ---
with tabs[2]:
    st.subheader("📈 Financial Ratio Analysis (Professional Methodology)")
    
    # Balance Sheet
    st.markdown("#### 🏛️ יחסי מאזן")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.metric("Current Ratio", "1.42")
        with st.expander("ℹ️ הסבר מקצועי"):
            st.write("**הגדרה:** נכסים שוטפים / התחייבויות שוטפות. בביטוח, בודק נזילות השקעות מול התחייבויות מיידיות.")
    with b2:
        st.metric("Equity to Assets", "11.8%")
        with st.expander("ℹ️ הסבר מקצועי"):
            st.write("**הגדרה:** הון עצמי / סך מאזן. מעיד על רמת המינוף והחוסן של החברה.")
    with b3:
        st.metric("Financial Leverage", "7.8x")
        with st.expander("ℹ️ הסבר מקצועי"):
            st.write("**הגדרה:** סך הנכסים / הון עצמי. מציין כמה נכסים מנוהלים על כל שקל הון.")

    st.divider()
    
    # P&L & Cash Flow
    st.markdown("#### 💰 יחסי רווחיות ותזרים")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("CFO to Net Profit", "1.15x")
        with st.expander("ℹ️ הסבר מקצועי"):
            st.write("**הגדרה:** תזרים מפעילות שוטפת / רווח נקי. בודק את 'איכות' הרווח והפיכתו למזומן.")
    with p2:
        st.metric("Combined Ratio", f"{row['Combined Ratio %']}%")
        with st.expander("ℹ️ הסבר מקצועי"):
            st.write("**הגדרה:** (תביעות + הוצאות) / פרמיות. המדד הקריטי לרווחיות חיתומית באלמנטר ובריאות.")
    with p3:
        st.metric("Free Cash Flow (M₪)", "1,180")
        with st.expander("ℹ️ הסבר מקצועי"):
            st.write("**הגדרה:** תזרים תפעולי פחות השקעות הון. המקור העיקרי לחלוקת דיבידנד.")

# --- TAB 4: STRESS SCENARIOS (FULL DATA) ---
with tabs[3]:
    st.subheader("🛡️ תרחישי קיצון ורגישות הון (Stress Suite)")
    col_in, col_res = st.columns([1, 1.2])
    with col_in:
        ir_s = st.slider("📉 ריבית (bps)", -100, 100, 0)
        mkt_s = st.slider("📉 מניות (%)", 0, 40, 0)
        spr_s = st.slider("📉 אשראי (Spread bps)", 0, 150, 0)
        lap_s = st.slider("📉 ביטולים (%)", 0, 20, 0)
        eq_s = st.checkbox("🌋 תרחיש רעידת אדמה (Catastrophe)")
    with col_res:
        imp = (ir_s * 0.12) + (mkt_s * -0.65) + (spr_s * -0.08) + (lap_s * -0.4) + (-15 if eq_s else 0)
        new_s = row['Solvency %'] + imp
        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number+delta", value = new_s, delta = {'reference': row['Solvency %']},
            gauge = {'axis': {'range': [80, 250]}, 'steps': [
                {'range': [80, 140], 'color': "red"},
                {'range': [170, 250], 'color': "green"}]}))
        st.plotly_chart(fig_g, use_container_width=True)
        st.caption(f"השפעה מצטברת חזויה: {imp:+.1f}%")

# --- TAB 5: AI HYBRID RESEARCH (VISION) ---
with tabs[4]:
    st.subheader("🤖 AI Hybrid Analyst (Vision + Note Scan)")
    if fin_paths:
        q = st.text_input("שאל שאלה על הביאורים (למשל: 'נתח את מרכיב ההפסד'): ")
        if q:
            with st.spinner("מנתח דפים וטבלאות..."):
                doc = fitz.open(fin_paths[0])
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.open(io.BytesIO(pix.tobytes()))
                res = ai_model.generate_content([f"אנליסט מומחה, נתח: {q}", img])
                st.write(res.text)
