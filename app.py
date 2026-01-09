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
# 1. SETUP & AI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise | Strategic AI Terminal", layout="wide")

def initialize_ai():
    """חיבור למנוע ה-AI באמצעות המפתח ב-Secrets"""
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
    """טעינת מודל ה-AI באופן יציב"""
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
    """חילוץ טקסט מ-50 דפים לאיתור נתוני מאזן עמוקים"""
    full_text = ""
    preview_images = []
    try:
        doc = fitz.open(pdf_path)
        for i in range(min(len(doc), 50)):
            full_text += f"\n--- Page {i+1} ---\n" + doc[i].get_text()
            if i < 5: # שמירת 5 דפים ראשונים לתצוגה ויזואלית
                pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                preview_images.append(Image.open(io.BytesIO(pix.tobytes())))
        return full_text, preview_images
    except Exception as e:
        return f"Error: {e}", []

# ==========================================
# 3. DATA WAREHOUSE (נתונים השוואתיים)
# ==========================================
market_df = pd.DataFrame({
    "company": ["Phoenix", "Harel", "Menora", "Clal", "Migdal"],
    "solvency": [184, 172, 175, 158, 149],
    "roe": [14.1, 11.8, 12.5, 10.2, 10.4],
    "csm": [14.8, 14.1, 9.7, 11.2, 11.5]
})

# ==========================================
# 4. SIDEBAR - FILE DETECTION
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    sel_comp = st.selectbox("בחר חברה:", market_df["company"])
    sel_year = st.selectbox("שנה:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # השם שהמערכת מחפשת ב-GitHub
    expected_filename = f"{sel_comp}_{sel_q}_{sel_year}.pdf"
    
    if os.path.exists(expected_filename):
        pdf_path = expected_filename
        st.success(f"✅ קובץ זוהה: {expected_filename}")
        file_ready = True
    else:
        pdf_path = None
        st.warning(f"⚠️ חסר קובץ ב-GitHub: {expected_filename}")
        file_ready = False

# ==========================================
# 5. MAIN INTERFACE
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

tabs = st.tabs(["📊 KPI Dashboard", "🤖 AI Deep Research"])

with tabs[0]:
    row = market_df[market_df["company"] == sel_comp].iloc[0]
    st.subheader("מדדי ליבה")
    k1, k2, k3 = st.columns(3)
    k1.metric("Solvency Ratio", f"{row['solvency']}%")
    k2.metric("ROE (תשואה להון)", f"{row['roe']}%")
    k3.metric("CSM Balance", f"NIS {row['csm']}B")
    st.plotly_chart(px.bar(market_df, x="company", y="solvency", color="company", title="השוואת חוסן הון"), use_container_width=True)

with tabs[1]:
    st.subheader("🤖 אנליסט AI - סריקה עמוקה")
    if file_ready:
        query = st.text_input("שאל שאלה מקצועית (למשל: מהו ההון העצמי המיוחס לבעלי המניות?)")
        if st.button("🚀 הרץ ניתוח עמוק") and query:
            if ai_model:
                with st.spinner("סורק את דפי המאזן..."):
                    full_text, pages = extract_deep_context(pdf_path)
                    if pages:
                        cols = st.columns(len(pages))
                        for idx, p in enumerate(pages): cols[idx].image(p, use_container_width=True)
                    
                    prompt = f"נתח את דוח {sel_comp}. אתר את הנתון 'הון עצמי המיוחס לבעלי המניות'. שאלה: {query}\n\nטקסט מהדוח: {full_text[:15000]}"
                    response = ai_model.generate_content(prompt)
                    st.success(response.text)
            else:
                st.error("AI לא מחובר - בדוק Secrets")
    else:
        st.info(f"העלה ל-GitHub את הדוח בשם המדויק: {expected_filename}")
