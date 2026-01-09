import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
import fitz  # PyMuPDF

# ==========================================
# 1. SETUP & AI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing API Key in Secrets")

# ==========================================
# 2. פונקציית איתור קבצים עם הגנה מכפילויות
# ==========================================
def find_pdf_smart(base_folder, target_name):
    """מחפש קובץ שמתחיל בשם המבוקש ומתעלם מכפילויות סיומת"""
    if not os.path.exists(base_folder):
        return None
    
    for f in os.listdir(base_folder):
        # בודק אם השם מתחיל נכון (למשל Clal_Q1_2025) ומסתיים ב-pdf
        if f.lower().startswith(target_name.lower()) and f.lower().endswith('.pdf'):
            return os.path.join(base_folder, f)
    return None

# ==========================================
# 3. SIDEBAR - ניווט
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    comp = st.selectbox("בחר חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    
    # הגדרת בסיס החיפוש
    base_dir = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(base_dir): # בדיקה גם עם Data גדולה
        base_dir = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"

    # חיפוש חכם שמתעלם מ-.pdf.pdf
    fin_target = f"{comp}_{q}_{year}"
    sol_target = f"Solvency_{comp}_{q}_{year}"
    
    path_fin = find_pdf_smart(f"{base_dir}/Financial_Reports", fin_target)
    path_sol = find_pdf_smart(f"{base_dir}/Solvency_Reports", sol_target)
    
    st.write(f"📄 דוח כספי: {'✅' if path_fin else '❌'}")
    if path_fin and ".pdf.pdf" in path_fin:
        st.caption("⚠️ זוהתה סיומת כפולה בקובץ, המערכת תתקן זאת אוטומטית.")
    
    st.write(f"🛡️ דוח סולבנסי: {'✅' if path_sol else '❌'}")

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title(f"🏛️ {comp} | Strategic AI Terminal")
t1, t2 = st.tabs(["📊 KPI Dashboard", "🤖 AI Analyst"])

with t2:
    st.subheader("ניתוח AI עמוק")
    mode = st.radio("בחר דוח:", ["כספי", "סולבנסי"])
    active_path = path_fin if mode == "כספי" else path_sol
    
    if active_path:
        st.success(f"מנתח את: {os.path.basename(active_path)}")
        query = st.text_input(f"שאל על ה{mode} (למשל: מהו ההון העצמי?):")
        
        if st.button("🚀 הרץ ניתוח") and query:
            with st.spinner("סורק נתונים..."):
                try:
                    doc = fitz.open(active_path)
                    text = "".join([page.get_text() for page in doc[:40]])
                    
                    # שימוש ב-KPI הקריטי שביקשת לשמור
                    prompt = f"נתח דוח {mode} של {comp}. מצא 'הון עצמי מיוחס לבעלי המניות'. שאלה: {query}\n\nטקסט: {text[:15000]}"
                    response = model.generate_content(prompt)
                    st.markdown("---")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה: {e}")
    else:
        st.warning("הקובץ לא נמצא בנתיב המבוקש ב-GitHub.")
