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
# 1. SETUP & SECURE AI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise | Strategic AI Terminal", layout="wide")

def initialize_ai():
    """בדיקת חיבור למפתח ה-API מתוך ה-Secrets של Streamlit"""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            if api_key and api_key != "your_key_here":
                genai.configure(api_key=api_key)
                return True
        return False
    except Exception:
        return False

ai_ready = initialize_ai()

@st.cache_resource
def get_stable_model():
    """טעינת מודל ה-AI באופן יציב למניעת שגיאות 404"""
    if not ai_ready:
        return None, "Missing API Key"
    # שם מודל תקני ל-Streamlit Cloud
    model_name = 'gemini-1.5-flash'
    try:
        model = genai.GenerativeModel(model_name)
        return model, model_name
    except Exception as e:
        return None, str(e)

ai_model, active_model_name = get_stable_model()

# ==========================================
# 2. PDF DEEP SCAN ENGINE
# ==========================================
def extract_deep_context(pdf_path):
    """חילוץ טקסט מ-50 דפים לאיתור נתונים עמוקים (מאזן)"""
    full_text = ""
    preview_images = []
    try:
        doc = fitz.open(pdf_path)
        for i in range(min(len(doc), 50)):
            full_text += f"\n--- Page {i+1} ---\n" + doc[i].get_text()
            if i < 5:
                pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                preview_images.append(Image.open(io.BytesIO(pix.tobytes())))
        return full_text, preview_images
    except Exception as e:
        return f"Error: {e}", []

# ==========================================
# 3. DATA WAREHOUSE (נתונים השוואתיים)
# ==========================================
# שמות העמודות באנגלית למניעת שגיאות Syntax עם תווים מיוחדים
market_df = pd.DataFrame({
    "company": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "solvency": [184, 172, 175, 158, 149],
    "roe": [14.1, 11.8, 12.5, 10.2, 10.4],
    "csm": [14.8, 14.1, 9.7, 11.2, 11.5]
})

# ==========================================
# 4. SIDEBAR - CONTROL PANEL
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    sel_comp = st.selectbox("בחר חברה:", market_df["company"])
    sel_year = st.selectbox("שנה:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    # נתיב חיפוש קבצים - מוגדר לחפש בתיקייה הראשית או תחת data
    pdf_filename = f"{sel_comp}_{sel_q}_{sel_year}.pdf"
    alt_path = f"data/Insurance_Warehouse/{sel_comp}/{sel_year}/{sel_q}/Financial_Reports/{pdf_filename}"
    
    if os.path.exists(pdf_filename):
        pdf_path = pdf_filename
        st.success(f"✅ זוהה קובץ: {pdf_filename}")
    elif os.path.exists(alt_path):
        pdf_path = alt_path
        st.success("✅ דוח זוהה בתיקייה")
    else:
        pdf_path = None
        st.warning(f"⚠️ חסר קובץ: {pdf_filename}")
        st.info("העלה את הקובץ ל-GitHub עם השם המדויק.")

# ==========================================
# 5. MAIN INTERFACE
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 KPI Dashboard", "🤖 AI Deep Research"])

# --- TAB 1: KPI Dashboard ---
with tabs[0]:
    row = market_df[market_df["company"] == sel_comp].iloc[0]
    st.subheader("מדדי ליבה (IFRS 17)")
    k1, k2, k3 = st.columns(3)
    k1.metric("Solvency Ratio", f"{row['solvency']}%")
    k2.metric("ROE (תשואה להון)", f"{row['roe']}%")
    k3.metric("CSM Balance", f"NIS {row['csm']}B")
    
    st.plotly_chart(px.bar(market_df, x="company", y="solvency", color="company", title="השוואת חוסן הון בענף"), use_container_width=True)

# --- TAB 2: AI DEEP RESEARCH ---
with tabs[1]:
    st.subheader("🤖 אנליסט AI היברידי (טקסט + ויז'ן)")
    if pdf_path:
        query = st.text_input("שאל על הנתונים (למשל: מהו ההון העצמי המיוחס לבעלי המניות?)")
        analyze_btn = st.button("🚀 הרץ ניתוח עמוק")
        
        if analyze_btn and query:
            if ai_model is None:
                st.error("ה-AI לא מחובר. וודא שהמפתח ב-Secrets תקין.")
            else:
                with st.spinner("סורק את דפי המאזן ומנתח נתונים..."):
                    full_text, pages = extract_deep_context(pdf_path)
                    
                    if pages:
                        st.caption("דפים שנסרקו לאנליזה:")
                        cols = st.columns(len(pages))
                        for idx, p in enumerate(pages):
                            cols[idx].image(p, use_container_width=True)
                    
                    prompt = f"""
                    אתה אנליסט ביטוח בכיר. נתח את הטקסט שחולץ מהדוח של {sel_comp}.
                    אתר את הנתון של "הון עצמי המיוחס לבעלי המניות" במאזן.
                    ענה בעברית מקצועית על השאלה: {query}
                    
                    טקסט מהדוח (50 דפים):
                    {full_text[:15000]}
                    """
                    try:
                        response = ai_model.generate_content(prompt)
                        st.markdown("---")
                        st.markdown("### 📝 תשובת האנליסט:")
                        st.success(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בהפעלת ה-AI: {e}")
    else:
        st.info("כדי להפעיל את האנליסט, העלה את קובץ ה-PDF ל-GitHub.")
