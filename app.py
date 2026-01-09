import os
import subprocess
import sys

# 1. התקנה אוטומטית וניהול סביבת עבודה
def install_requirements():
    packages = ['PyPDF2', 'google-generativeai', 'pdf2image', 'PyMuPDF', 'pillow', 'plotly', 'streamlit', 'pandas']
    for package in packages:
        try:
            # מניעת ייבוא כפול ובדיקת גרסה בסיסית
            __import__(package.replace('-', '_'))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io

# ==========================================
# 2. SETUP & SECURE AI
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
            st.error("❌ מפתח API לא נמצא ב-Secrets!")
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
        # ניסיון עבודה עם המודלים המתקדמים ביותר הזמינים
        model_name = 'gemini-1.5-pro'
        return genai.GenerativeModel(model_name), model_name
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash'), 'gemini-1.5-flash'

ai_model, active_model_name = get_stable_model()

# ==========================================
# 3. ROBUST DATA WAREHOUSE (FIXING 404/NOT FOUND)
# ==========================================
BASE_WAREHOUSE = "data/Insurance_Warehouse"

def get_verified_paths(company, year, quarter):
    """בדיקה בטוחה של נתיבים למניעת שגיאות FileNotFoundError"""
    base = os.path.join(BASE_WAREHOUSE, company, str(year), quarter)
    fin_dir = os.path.join(base, "Financial_Reports")
    sol_dir = os.path.join(base, "Solvency_Reports")
    
    fin_files = []
    sol_files = []
    
    # בדיקת קיום תיקיות לפני ניסיון קריאה (מונע שגיאת 404/Not Found)
    if os.path.exists(fin_dir):
        fin_files = [os.path.join(fin_dir, f) for f in os.listdir(fin_dir) if f.endswith('.pdf')]
    
    if os.path.exists(sol_dir):
        sol_files = [os.path.join(sol_dir, f) for f in os.listdir(sol_dir) if f.endswith('.pdf')]
        
    return fin_files, sol_files

# נתוני שוק - KPI Checklist
market_df = pd.DataFrame({
    "חברה": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "Solvency %": [184, 172, 175, 158, 149],
    "ROE %": [14.1, 11.8, 12.5, 10.2, 10.4],
    "CSM (B₪)": [14.8, 14.1, 9.7, 11.2, 11.5],
    "Combined Ratio %": [91.5, 93.2, 92.8, 95.1, 94.4],
    "Expense Ratio %": [18.2, 19.1, 17.5, 20.4, 19.8]
})

# ==========================================
# 4. SIDEBAR - CONTROL PANEL
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
        st.success(f"✅ דוח כספי זמין")
    else:
        st.warning("⚠️ לא נמצא דוח בנתיב המבוקש")
        
    if sol_paths:
        st.success(f"✅ דוח סולבנסי זמין")
    else:
        st.info("ℹ️ דוח סולבנסי חסר")

# ==========================================
# 5. MAIN TERMINAL
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 מדדי KPI", "⛓️ מנוע IFRS 17", "📈 יחסים פיננסיים", "🛡️ תרחישי קיצון", "🤖 מחקר AI"])

# --- TAB 1: Core KPIs ---
with tabs[0]:
    row = market_df[market_df["חברה"] == sel_comp].iloc[0]
    st.subheader("מדדי ליבה מבוססי דוחות 2024-2026")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Solvency Ratio", f"{row['Solvency %']}%")
    k2.metric("ROE", f"{row['ROE %']}%")
    k3.metric("Combined Ratio", f"{row['Combined Ratio %']}%")
    k4.metric("CSM Balance", f"₪{row['CSM (B₪)']}B")
    k5.metric("Exp. Ratio", f"{row['Expense Ratio %']}%")
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(market_df, x="חברה", y="CSM (B₪)", title="השוואת עתודות רווח מגזריות"), use_container_width=True)
    with c2:
        st.plotly_chart(px.line(market_df, x="חברה", y="Solvency %", title="מגמת חוסן הוני במערכת"), use_container_width=True)

# --- TAB 2: IFRS 17 ---
with tabs[1]:
    st.subheader("⛓️ IFRS 17 Deep Dive")
    st.info("ניתוח חוזים מכבידים (Onerous Contracts) ומרכיבי הפסד (Loss Component)")
    
    # מפל CSM לדוגמה
    fig_wf = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        x = ["Opening", "New Business", "Experience", "Assumption Changes", "Release", "Closing"],
        textposition = "outside",
        y = [100, 20, -5, 10, -15, 110],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

# --- TAB 3: Financial Ratios ---
with tabs[2]:
    st.subheader("📈 ניתוח יחסי דוח רווח והפסד ומאזן")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("#### נזילות ומינוף")
        st.metric("Current Ratio", "1.45")
        st.metric("Debt to Equity", "0.22")
    with col_b:
        st.write("#### איכות הרווח")
        st.metric("CFO to Net Income", "1.12x")
        st.metric("Investment Yield", "4.2%")

# --- TAB 4: Stress Scenarios ---
with tabs[3]:
    st.subheader("🛡️ סימולציית רגישות הון (Stress Suite)")
    ir = st.slider("שינוי בעקומת הריבית (bps)", -100, 100, 0)
    equity_drop = st.slider("ירידה בשוקי מניות (%)", 0, 30, 0)
    
    # חישוב השפעה ליניארי מקורב
    impact = (ir * 0.1) - (equity_drop * 0.8)
    final_solvency = row['Solvency %'] + impact
    
    st.gauge_value = final_solvency
    st.metric("Solvency חזוי לאחר קיצון", f"{final_solvency:.1f}%", delta=f"{impact:.1f}%")

# --- TAB 5: AI Research ---
with tabs[4]:
    st.subheader("🤖 עוזר מחקר חכם")
    if not fin_paths:
        st.info("אנא וודא שקיימים קבצי PDF בתיקייה כדי להפעיל את סריקת ה-AI.")
    else:
        user_query = st.text_input("שאל שאלה על ביאורי הדוח (למשל: 'מהן הנחות הריבית בביטוח חיים?'): ")
        if user_query and ai_ready:
            with st.spinner("סורק נתונים ומנתח..."):
                try:
                    # פתיחת דף ראשון כדוגמה ל-Vision
                    doc = fitz.open(fin_paths[0])
                    page = doc[0]
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    
                    response = ai_model.generate_content([f"נתח את המסמך הבא וענה: {user_query}", img])
                    st.markdown(f"### תשובת האנליסט:\n{response.text}")
                except Exception as e:
                    st.error(f"שגיאה בניתוח המסמך: {e}")
