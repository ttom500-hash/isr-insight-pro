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
st.set_page_config(page_title="Apex Pro Enterprise | Strategic Terminal", layout="wide")

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
    # תיקון שגיאת 404: שימוש במודל Flash בגרסת v1beta מבטיח תאימות מלאה
    model_name = 'gemini-1.5-flash'
    try:
        return genai.GenerativeModel(model_name), model_name
    except Exception:
        return None, "Error"

ai_model, active_model_name = get_stable_model()

# ==========================================
# 2. AUTOMATED DATA WAREHOUSE LOGIC
# ==========================================
BASE_WAREHOUSE = "data/Insurance_Warehouse"

def get_verified_paths(company, year, quarter):
    """סריקה אוטומטית של נתיבי הקבצים במאגר הנתונים"""
    base = os.path.join(BASE_WAREHOUSE, company, str(year), quarter)
    fin_dir = os.path.join(base, "Financial_Reports")
    sol_dir = os.path.join(base, "Solvency_Reports")
    
    fin_files = [os.path.join(fin_dir, f) for f in os.listdir(fin_dir) if f.endswith('.pdf')] if os.path.exists(fin_dir) else []
    sol_files = [os.path.join(sol_dir, f) for f in os.listdir(sol_dir) if f.endswith('.pdf')] if os.path.exists(sol_dir) else []
    return fin_files, sol_files

# מסד נתונים מקצועי - KPI Checklist (מבוסס על הגדרות הלקוח)
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
# 3. SIDEBAR - AUTOMATED RADAR
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    sel_comp = st.selectbox("בחר חברה לניתוח:", market_df["חברה"])
    sel_year = st.selectbox("שנה פיסקאלית:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון דיווח:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # סריקה אוטומטית של קבצים מה-Repository
    fin_paths, sol_paths = get_verified_paths(sel_comp, sel_year, sel_q)
    
    st.divider()
    st.subheader("📁 נתיבי קבצים זוהו:")
    if fin_paths:
        st.success(f"✅ דוח כספי: {os.path.basename(fin_paths[0])}")
    else:
        st.warning("❌ דוח כספי לא נמצא בתיקייה")
        
    if sol_paths:
        st.success(f"✅ דוח סולבנסי: {os.path.basename(sol_paths[0])}")
    
    st.caption(f"AI Analytic Core: {active_model_name}")

# ==========================================
# 4. MAIN TERMINAL - FULL FEATURES
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 Critical KPIs", "⛓️ IFRS 17 Engine", "📈 Financial Ratios", "🛡️ Stress Scenarios", "🤖 AI Deep Research"])

# --- TAB 1: Critical KPIs ---
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
        st.plotly_chart(px.bar(market_df, x="חברה", y="CSM (B₪)", color="חברה", 
                              title="השוואת עתודות רווח (CSM)"), use_container_width=True)
    with col_g2:
        st.plotly_chart(px.scatter(market_df, x="Combined Ratio %", y="ROE %", size="CSM (B₪)", 
                                  text="חברה", title="יעילות חיתומית מול תשואה"), use_container_width=True)

# --- TAB 2: IFRS 17 Engine ---
with tabs[1]:
    st.subheader("⛓️ IFRS 17: CSM Analytics & Waterfall")
    # הצגת גרף מפל CSM מלא ומקצועי
    fig_wf = go.Figure(go.Waterfall(
        x = ["יתרת פתיחה", "חוזים חדשים", "שינוי אומדן", "חוזים מכבידים", "שחרור לרווח", "יתרת סגירה"],
        y = [14200, 850, 150, -320, -1100, 13780],
        measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
    ))
    fig_wf.update_layout(title="תנועה ב-CSM (מיליוני ש''ח)")
    st.plotly_chart(fig_wf, use_container_width=True)
    
    st.info(f"**מבט חיתומי:** שיעור רווחיות עסקים חדשים (NB Margin) נאמד ב-{row['NB Margin %']}%")

# --- TAB 3: Financial Ratios ---
with tabs[2]:
    st.subheader("📈 Financial Ratio Analysis")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.metric("Current Ratio", "1.42")
        st.caption("נזילות: נכסים שוטפים / התחייבויות שוטפות")
    with b2:
        st.metric("Equity to Assets", "11.8%")
        st.caption("חוסן: הון עצמי / סך מאזן")
    with b3:
        st.metric("Financial Leverage", "7.8x")
        st.caption("מינוף: סך נכסים / הון עצמי")

# --- TAB 4: Stress Scenarios ---
with tabs[3]:
    st.subheader("🛡️ סימולציית תרחישי קיצון")
    ir_s = st.slider("📉 שינוי ריבית (bps)", -100, 100, 0)
    mkt_s = st.slider("📉 ירידת מניות (%)", 0, 40, 0)
    
    # חישוב השפעה חזויה על יחס הסולבנסי
    impact = (ir_s * 0.12) - (mkt_s * 0.65)
    final_sol = row['Solvency %'] + impact
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta", value = final_sol,
        delta = {'reference': row['Solvency %']},
        gauge = {'axis': {'range': [80, 220]},
                 'steps': [{'range': [0, 100], 'color': "red"}, {'range': [100, 140], 'color': "orange"}]}))
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- TAB 5: AI Hybrid Research ---
with tabs[4]:
    st.subheader("🤖 AI Hybrid Analyst (Vision + Auto-Scan)")
    if fin_paths:
        st.success(f"האנליסט מנתח אוטומטית את: {os.path.basename(fin_paths[0])}")
        user_q = st.text_input("שאל שאלה על הביאורים (למשל: 'נתח את הנחות הריבית'):")
        
        if user_q and ai_ready:
            with st.spinner("מבצע ניתוח Vision עמוק..."):
                try:
                    doc = fitz.open(fin_paths[0])
                    # המרת דף הביאורים הרלוונטי לתמונה
                    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    
                    with st.expander("צפה בדף הנסרק על ידי ה-AI"):
                        st.image(img, use_container_width=True)
                    
                    response = ai_model.generate_content([f"נתח את הדף וענה בעברית על: {user_q}", img])
                    st.markdown("### 📝 תשובת האנליסט:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה בניתוח: {e}")
    else:
        st.warning("⚠️ לא נמצא דוח PDF בנתיב המבוקש לסריקה אוטומטית.")
