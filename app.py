import os
import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io

# ==========================================
# 1. SETUP & AI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise | Strategic AI Terminal", layout="wide")

def initialize_ai():
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
    if not ai_ready: return None, "Missing API Key"
    model_name = 'gemini-1.5-flash'
    try:
        return genai.GenerativeModel(model_name), model_name
    except Exception as e:
        return None, str(e)

ai_model, active_model_name = get_stable_model()

# ==========================================
# 2. PDF DEEP SCAN ENGINE
# ==========================================
def extract_deep_context(pdf_path):
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
# 3. SIDEBAR - ניווט תיקיות חכם (תואם למבנה שלך)
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    sel_comp = st.selectbox("בחר חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    sel_year = st.selectbox("שנה:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    
    # בניית נתיבים לפי המבנה שציינת
    base_path = f"data/Insurance_Warehouse/{sel_comp}/{sel_year}/{sel_q}"
    
    fin_file = f"{sel_comp}_{sel_q}_{sel_year}.pdf"
    fin_path = f"{base_path}/Financial_Reports/{fin_file}"
    
    sol_file = f"Solvency_{sel_comp}_{sel_q}_{sel_year}.pdf"
    sol_path = f"{base_path}/Solvency_Reports/{sol_file}"
    
    # בדיקת נוכחות קבצים
    st.subheader("סטטוס קבצים:")
    
    has_fin = os.path.exists(fin_path)
    if has_fin: st.success(f"✅ דוח כספי זוהה")
    else: st.warning(f"❌ חסר דוח כספי")
    
    has_sol = os.path.exists(sol_path)
    if has_sol: st.success(f"✅ דוח סולבנסי זוהה")
    else: st.warning(f"❌ חסר דוח סולבנסי")

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 KPI Dashboard", "🤖 AI Deep Research"])

with tabs[0]:
    st.subheader("מדדי ליבה והשוואת שוק")
    st.info("כאן יוצגו נתונים ויזואליים מתוך מסד הנתונים.")
    # כאן ניתן להוסיף את הגרפים שהיו לנו קודם

with tabs[1]:
    st.subheader("🤖 אנליסט AI - סריקה משולבת")
    
    report_type = st.radio("בחר דוח לניתוח:", ["דוח כספי (הון עצמי, רווח)", "דוח סולבנסי (יחס הון)"])
    
    active_path = fin_path if "כספי" in report_type else sol_path
    file_to_scan = has_fin if "כספי" in report_type else has_sol
    
    if file_to_scan:
        query = st.text_input("שאל את ה-AI על הדוח הנבחר:")
        if st.button("🚀 הרץ ניתוח עמוק") and query:
            if ai_model:
                with st.spinner(f"סורק את {report_type}..."):
                    full_text, pages = extract_deep_context(active_path)
                    
                    # הצגת דפי שער להמחשה
                    cols = st.columns(len(pages))
                    for idx, p in enumerate(pages): cols[idx].image(p, use_container_width=True)
                    
                    prompt = f"""
                    נתח את הדוח של חברת {sel_comp}.
                    במידה וזה דוח כספי, אתר 'הון עצמי'. במידה וזה סולבנסי, אתר 'יחס כושר פירעון'.
                    ענה בעברית על השאלה: {query}
                    
                    טקסט מהדוח:
                    {full_text[:15000]}
                    """
                    response = ai_model.generate_content(prompt)
                    st.success(response.text)
            else: st.error("AI מנותק - בדוק Secrets")
    else:
        st.error(f"לא נמצא קובץ PDF בנתיב: {active_path}")
