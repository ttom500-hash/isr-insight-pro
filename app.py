import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
import fitz  # PyMuPDF
from PIL import Image
import io

# ==========================================
# 1. SETUP & AI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

def initialize_ai():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            return genai.GenerativeModel('gemini-1.5-flash')
        return None
    except Exception:
        return None

model = initialize_ai()

# ==========================================
# 2. פונקציית חיפוש קבצים גמישה
# ==========================================
def find_pdf_path(company, year, quarter, report_type):
    """מחפש את הקובץ בכמה וריאציות של נתיבים"""
    
    # הגדרת שמות הקבצים המצופים
    if report_type == "כספי":
        filename = f"{company}_{quarter}_{year}.pdf"
        sub_folder = "Financial_Reports"
    else:
        filename = f"Solvency_{company}_{quarter}_{year}.pdf"
        sub_folder = "Solvency_Reports"

    # רשימת נתיבים אפשריים לבדיקה (כולל Data באות גדולה)
    possible_paths = [
        f"data/Insurance_Warehouse/{company}/{year}/{quarter}/{sub_folder}/{filename}",
        f"Data/Insurance_Warehouse/{company}/{year}/{quarter}/{sub_folder}/{filename}",
        f"data/insurance_warehouse/{company}/{year}/{quarter}/{sub_folder}/{filename}",
        filename # בדיקה גם בתיקייה הראשית
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

# ==========================================
# 3. SIDEBAR - ניווט
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    sel_comp = st.selectbox("בחר חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    sel_year = st.selectbox("שנה:", [2024, 2025, 2026])
    sel_q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    
    # חיפוש שני סוגי הדוחות
    path_fin = find_pdf_path(sel_comp, sel_year, sel_q, "כספי")
    path_sol = find_pdf_path(sel_comp, sel_year, sel_q, "סולבנסי")
    
    st.write(f"📄 דוח כספי: {'✅' if path_fin else '❌'}")
    st.write(f"🛡️ דוח סולבנסי: {'✅' if path_sol else '❌'}")
    
    if not path_fin and not path_sol:
        st.info("💡 טיפ: וודא שהנתיב ב-GitHub תואם בדיוק למבנה התיקיות.")

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title(f"🏛️ {sel_comp} | Strategic AI Terminal")

t1, t2 = st.tabs(["📊 KPI Dashboard", "🤖 AI Analyst"])

with t2:
    st.subheader("ניתוח דוחות עמוק")
    
    report_mode = st.radio("סוג דוח לניתוח:", ["כספי", "סולבנסי"])
    active_path = path_fin if report_mode == "כספי" else path_sol
    
    if active_path:
        query = st.text_input(f"שאל על דוח ה{report_mode} (למשל: מהו ההון העצמי?):")
        
        if st.button("🚀 הרץ ניתוח עמוק") and query:
            if model:
                with st.spinner("סורק דפים ומחלץ נתונים..."):
                    try:
                        doc = fitz.open(active_path)
                        # סריקת 40 עמודים ראשונים לטקסט
                        text_content = ""
                        for i in range(min(len(doc), 40)):
                            text_content += doc[i].get_text()
                        
                        prompt = f"""
                        אתה אנליסט בכיר. נתח את דוח ה{report_mode} של חברת {sel_comp}.
                        התמקד ב-5 ה-KPIs הקריטיים (הון עצמי, סולבנסי, רווח כולל).
                        שאלה: {query}
                        
                        טקסט מהדוח:
                        {text_content[:15000]}
                        """
                        
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.success(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בקריאת הקובץ: {e}")
            else:
                st.error("ה-AI לא מוגדר. בדוק את ה-API Key ב-Secrets.")
    else:
        st.warning(f"לא נמצא קובץ {report_mode} עבור {sel_comp} לנתוני {sel_q} {sel_year}.")
