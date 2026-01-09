import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io

# ==========================================
# 1. SETUP & SECURE AI
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise v2", layout="wide")

def initialize_ai():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
            return True
        return False
    except Exception:
        return False

ai_ready = initialize_ai()

@st.cache_resource
def get_stable_model():
    if not ai_ready: return None, "None"
    # שימוש ב-flash ליציבות מול שגיאות 404
    model_name = 'gemini-1.5-flash'
    return genai.GenerativeModel(model_name), model_name

ai_model, active_model_name = get_stable_model()

# ==========================================
# 2. DATA WAREHOUSE LOGIC
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
    "Expense Ratio %": [18.2, 19.1, 17.5, 20.4, 19.8]
})

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("🛡️ Control Panel")
    sel_comp = st.selectbox("בחר חברה:", market_df["חברה"])
    sel_year = st.selectbox("שנה:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    fin_paths, sol_paths = get_verified_paths(sel_comp, sel_year, sel_q)
    
    st.divider()
    if fin_paths: st.success("✅ דוח כספי זוהה")
    else: st.warning("⚠️ המתן להעלאת דוח")
    st.caption(f"AI: {active_model_name}")

# ==========================================
# 4. MAIN TERMINAL
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 מדדי KPI", "⛓️ מנוע IFRS 17", "📈 יחסים פיננסיים", "🛡️ תרחישי קיצון", "🤖 מחקר AI"])

# --- TAB 1: Core KPIs ---
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
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(market_df, x="חברה", y="CSM (B₪)", color="חברה", title="השוואת עתודות רווח (CSM)"), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(values=[60, 25, 15], names=["Life", "Health", "P&C"], title="Profit Mix"), use_container_width=True)

# --- TAB 2: IFRS 17 ENGINE ---
with tabs[1]:
    st.subheader("⛓️ IFRS 17: CSM Analytics & Loss Component")
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.info("**VFA Approach**\n\nחיסכון ארוך טווח")
    m_col2.success("**GMM Approach**\n\nריסק וסיעוד")
    m_col3.warning("**PAA Approach**\n\nאלמנטר ובריאות")
    
    fig_wf = go.Figure(go.Waterfall(
        x = ["יתרת פתיחה", "חוזים חדשים", "חוזים מכבידים", "שחרור לרווח", "יתרת סגירה"],
        y = [14200, 850, -320, -1100, 13630],
        measure = ["absolute", "relative", "relative", "relative", "total"]
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

# --- TAB 3: FINANCIAL RATIOS ---
with tabs[2]:
    st.subheader("📈 Financial Ratio Analysis")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.metric("Current Ratio", "1.42")
        with st.expander("ℹ️ הסבר"): st.write("נכסים שוטפים / התחייבויות שוטפות")
    with b2:
        st.metric("Equity to Assets", "11.8%")
        with st.expander("ℹ️ הסבר"): st.write("הון עצמי / סך מאזן")
    with b3:
        st.metric("Financial Leverage", "7.8x")
        with st.expander("ℹ️ הסבר"): st.write("סך נכסים / הון עצמי")

# --- TAB 4: STRESS SCENARIOS ---
with tabs[3]:
    st.subheader("🛡️ תרחישי קיצון (Stress Suite)")
    ir_s = st.slider("📉 ריבית (bps)", -100, 100, 0)
    mkt_s = st.slider("📉 מניות (%)", 0, 40, 0)
    
    impact = (ir_s * 0.12) - (mkt_s * 0.7)
    new_s = row['Solvency %'] + impact
    
    fig_g = go.Figure(go.Indicator(
        mode = "gauge+number+delta", value = new_s,
        delta = {'reference': row['Solvency %']},
        gauge = {'axis': {'range': [80, 220]},
                 'steps': [{'range': [0, 100], 'color': "red"}, {'range': [100, 140], 'color': "orange"}]}))
    st.plotly_chart(fig_g, use_container_width=True)

# --- TAB 5: AI RESEARCH (VISION) ---
with tabs[4]:
    st.subheader("🤖 AI Vision Analyst")
    if fin_paths:
        query = st.text_input("שאל את האנליסט על הדוח:")
        if query and ai_ready:
            with st.spinner("סורק דף ראשון..."):
                try:
                    doc = fitz.open(fin_paths[0])
                    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    st.image(img, caption="הדף הנסרק", width=400)
                    
                    res = ai_model.generate_content([f"נתח בעברית: {query}", img])
                    st.success("תשובה:")
                    st.write(res.text)
                except Exception as e: st.error(f"שגיאה: {e}")
    else: st.info("העלה דוח PDF להפעלת הניתוח")
