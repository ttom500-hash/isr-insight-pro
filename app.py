import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
import fitz  # PyMuPDF

# ==========================================
# 1. SETUP & AI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

def initialize_ai():
    """חיבור יציב למנוע ה-AI ללא שגיאות גרסה"""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
            # שימוש בשם המודל ללא קידומות גרסה פותר את שגיאת ה-404
            return genai.GenerativeModel('gemini-1.5-flash')
        return None
    except Exception:
        return None

model = initialize_ai()

# ==========================================
# 2. פונקציית איתור קבצים חכמה
# ==========================================
def find_pdf_smart(base_folder, target_name):
    """מוצא קובץ בתיקייה ומתגבר על סיומות כפולות (.pdf.pdf)"""
    if not os.path.exists(base_folder):
        return None
    for f in os.listdir(base_folder):
        if f.lower().startswith(target_name.lower()) and f.lower().endswith('.pdf'):
            return os.path.join(base_folder, f)
    return None

# ==========================================
# 3. SIDEBAR - ניווט (תואם למבנה התיקיות שלך)
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    comp = st.selectbox("בחר חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # בדיקת נתיבים ב-GitHub (מטפל ב-data קטן וגדול)
    base_dir = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(base_dir):
        base_dir = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"

    path_fin = find_pdf_smart(f"{base_dir}/Financial_Reports", f"{comp}_{q}_{year}")
    path_sol = find_pdf_smart(f"{base_dir}/Solvency_Reports", f"Solvency_{comp}_{q}_{year}")
    
    st.write(f"📄 דוח כספי: {'✅' if path_fin else '❌'}")
    st.write(f"🛡️ דוח סולבנסי: {'✅' if path_sol else '❌'}")

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title(f"🏛️ {comp} | Strategic AI Terminal")
t1, t2 = st.tabs(["📊 KPI Dashboard", "🤖 AI Analyst"])

with t2:
    mode = st.radio("בחר סוג דוח:", ["כספי", "סולבנסי"])
    active_path = path_fin if mode == "כספי" else path_sol
    
    if active_path:
        st.success(f"מנתח את: {os.path.basename(active_path)}")
        query = st.text_input(f"שאל על ה{mode} (למשל: מהו ההון העצמי?):")
        
        if st.button("🚀 הרץ ניתוח") and query:
            if model:
                with st.spinner("סורק דפי מאזן ומחלץ נתונים..."):
                    try:
                        doc = fitz.open(active_path)
                        # חילוץ טקסט מ-40 עמודים ראשונים (איפה שההון העצמי נמצא)
                        text = "".join([page.get_text() for page in doc[:40]])
                        
                        prompt = f"""
                        אתה אנליסט ביטוח. נתח את דוח ה{mode} של {comp}.
                        אתר את הנתון 'הון עצמי מיוחס לבעלי המניות'.
                        שאלה: {query}
                        
                        טקסט מהדוח:
                        {text[:15000]}
                        """
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.success(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בתהליך: {e}")
            else:
                st.error("ה-AI לא מוגדר. בדוק את ה-API Key ב-Secrets.")
    else:
        st.warning("הקובץ לא נמצא בתיקייה המבוקשת.")
