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

# פונקציית עזר לטיפול במפתחות וחיבור למודל
def initialize_ai():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
            return True
        else:
            st.error("❌ מפתח API לא נמצא ב-Secrets! הגדר אותו ב-Streamlit Cloud Dashboard.")
            return False
    except Exception as e:
        st.error(f"❌ שגיאת אתחול AI: {e}")
        return False

ai_ready = initialize_ai()

@st.cache_resource
def get_stable_model():
    if not ai_ready:
        return None, "Not Configured"
    try:
        # עדיפות ל-1.5 Pro עבור ניתוח מסמכים מורכבים
        model_name = 'gemini-1.5-pro'
        return genai.GenerativeModel(model_name), model_name
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash'), 'gemini-1.5-flash'

ai_model, active_model_name = get_stable_model()

# ==========================================
# 2. DATA WAREHOUSE LOGIC (FIXED 404)
# ==========================================
BASE_WAREHOUSE = "data/Insurance_Warehouse"

def get_verified_paths(company, year, quarter):
    """בדיקה בטוחה של נתיבים למניעת שגיאות 404"""
    base = os.path.join(BASE_WAREHOUSE, company, str(year), quarter)
    fin_dir = os.path.join(base, "Financial_Reports")
    sol_dir = os.path.join(base, "Solvency_Reports")
    
    fin_files = []
    sol_files = []
    
    if os.path.exists(fin_dir):
        fin_files = [os.path.join(fin_dir, f) for f in os.listdir(fin_dir) if f.endswith('.pdf')]
    
    if os.path.exists(sol_dir):
        sol_files = [os.path.join(sol_dir, f) for f in os.listdir(sol_dir) if f.endswith('.pdf')]
        
    return fin_files, sol_files

# נתוני שוק - KPI Checklist (מבוסס על ההגדרות שביקשת לשמור)
market_df = pd.DataFrame({
    "חברה": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "Solvency %": [184, 172, 175, 158, 149],
    "ROE %": [14.1, 11.8, 12.5, 10.2, 10.4],
    "CSM (B₪)": [14.8, 14.1, 9.7, 11.2, 11.5],
    "Combined Ratio %": [91.5, 93.2, 92.8, 95.1, 94.4],
    "Expense Ratio %": [18.2, 19.1, 17.5, 20.4, 19.8]
})

# ==========================================
# 3. SIDEBAR - CONTROL PANEL
# ==========================================
with st.sidebar:
    st.header("🛡️ System Control")
    sel_comp = st.selectbox("בחר חברה לניתוח:", market_df["חברה"])
    sel_year = st.selectbox("שנה פיסקאלית:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון דיווח:", options=["Q1", "Q2", "Q3", "Q4"])
    
    fin_paths, sol_paths = get_verified_paths(sel_comp, sel_year, sel_q)
    
    st.divider()
    st.subheader("📁 Database Radar")
    if fin_paths:
        st.success(f"✅ דוח כספי זוהה")
    else:
        st.warning("⚠️ המתן להעלאת דוח לנתיב")
        
    st.caption(f"Active Model: {active_model_name}")

# ==========================================
# 4. MAIN TERMINAL (IFRS 17 & ANALYSIS)
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 מדדי KPI", "⛓️ מנוע IFRS 17", "📈 יחסים פיננסיים", "🛡️ תרחישי קיצון", "🤖 מחקר AI"])

# --- TAB 1: Core KPIs ---
with tabs[0]:
    row = market_df[market_df["חברה"] == sel_comp].iloc[0]
    st.subheader("מדדי ליבה - מבט מערכתי")
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
        # גרף פיזור להמחשת יעילות מול חוסן
        st.plotly_chart(px.scatter(market_df, x="Combined Ratio %", y="ROE %", size="CSM (B₪)", text="חברה", title="יעילות חיתומית מול תשואה להון"), use_container_width=True)

# --- TAB 2: IFRS 17 ENGINE ---
with tabs[1]:
    st.subheader("⛓️ IFRS 17: CSM Analytics & Loss Component")
    st.write("ניתוח דינמי של תנועת ה-CSM וחוזים מכבידים (Onerous Contracts)")
    
    col_wf, col_txt = st.columns([2, 1])
    with col_wf:
        fig_wf = go.Figure(go.Waterfall(
            orientation = "v",
            x = ["Opening", "New Business", "Experience", "Assumption Changes", "Release", "Closing"],
            y = [14200, 850, -120, 310, -1100, 14140],
            measure = ["absolute", "relative", "relative", "relative", "relative", "total"]
        ))
        st.plotly_chart(fig_wf, use_container_width=True)
    with col_txt:
        st.error("**Loss Component Alert**")
        st.write("במגזר ביטוח הבריאות זוהתה עלייה בחוזים מכבידים. מרכיב ההפסד נאמד ב-320 מיליון ש''ח.")

# --- TAB 3: Financial Ratios ---
with tabs[2]:
    st.subheader("📈 Financial Ratio Analysis")
    b1, b2, b3 = st.columns(3)
    b1.metric("Current Ratio", "1.42", help="נכסים שוטפים חלקי התחייבויות שוטפות")
    b2.metric("Financial Leverage", "7.8x", help="סך נכסים חלקי הון עצמי")
    b3.metric("Equity to Assets", "11.8%")

# --- TAB 4: Stress Scenarios ---
with tabs[3]:
    st.subheader("🛡️ סימולציית Stress Scenarios")
    ir_s = st.slider("📉 שינוי ריבית (bps)", -100, 100, 0)
    mkt_s = st.slider("📉 ירידת מניות (%)", 0, 40, 0)
    
    # חישוב השפעה
    total_impact = (ir_s * 0.12) - (mkt_s * 0.7)
    current_sol = row['Solvency %']
    new_sol = current_sol + total_impact
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = new_sol,
        delta = {'reference': current_sol},
        title = {'text': "Solvency II Ratio After Stress"},
        gauge = {'axis': {'range': [80, 220]},
                 'steps': [
                     {'range': [80, 100], 'color': "darkred"},
                     {'range': [100, 140], 'color': "orange"},
                     {'range': [140, 220], 'color': "green"}]}))
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- TAB 5: AI Research ---
with tabs[4]:
    st.subheader("🤖 AI Vision Analyst")
    if fin_paths:
        query = st.text_input("שאל את ה-AI על נתוני הדוח:")
        if query and ai_ready:
            with st.spinner("מנתח דפים רלוונטיים..."):
                try:
                    doc = fitz.open(fin_paths[0])
                    # המרה של דף הביאורים הראשון לתמונה עבור ה-Vision
                    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    
                    response = ai_model.generate_content([f"אנליסט מומחה, ענה על: {query}", img])
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"שגיאה בניתוח: {e}")
    else:
        st.info("העלה דוח PDF לתיקיית הדאטה כדי להפעיל את יכולות המחקר.")
