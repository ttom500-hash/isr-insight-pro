import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור גמיש (מונע את השגיאה הקריטית) ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# מנסה למשוך את המפתח מכל שם אפשרי ששמרת ב-Secrets
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY") or st.secrets.get("A")

if not api_key:
    st.error("⛔ שגיאה: המפתח לא נמצא ב-Secrets. וודא שכתוב: GOOGLE_API_KEY = '...'")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- 2. מנוע סריקת קבצים (מחינו את 'אין כלום') ---
BASE_DIR = "data/Insurance_Warehouse"

def get_hierarchy():
    hierarchy = {}
    if os.path.exists(BASE_DIR):
        for company in os.listdir(BASE_DIR):
            c_path = os.path.join(BASE_DIR, company)
            if os.path.isdir(c_path):
                hierarchy[company] = {}
                for year in os.listdir(c_path):
                    y_path = os.path.join(c_path, year)
                    if os.path.isdir(y_path):
                        hierarchy[company][year] = ["Q1", "Q2", "Q3", "Q4"]
    return hierarchy

# --- 3. ממשק צד (ניווט) ---
with st.sidebar:
    st.header("📂 ארכיון נתונים")
    data_map = get_hierarchy()
    
    full_path = None
    if data_map:
        comp = st.selectbox("בחר חברה:", list(data_map.keys()))
        year = st.selectbox("בחר שנה:", sorted(list(data_map[comp].keys()), reverse=True))
        q = st.selectbox("בחר רבעון:", data_map[comp][year])
        
        report_dir = os.path.join(BASE_DIR, comp, year, q, "Financial_Reports")
        if os.path.exists(report_dir):
            files = [f for f in os.listdir(report_dir) if f.endswith(".pdf")]
            if files:
                selected_file = st.selectbox("בחר דוח:", files)
                full_path = os.path.join(report_dir, selected_file)
            else:
                st.warning("לא נמצאו קבצי PDF.")
    else:
        st.error("לא נמצאה תיקיית נתונים ב-GitHub.")

# --- 4. פונקציית הניתוח ---
def analyze(path, prompt):
    with st.spinner("מנתח נתונים ברמה אקטוארית..."):
        try:
            f = genai.upload_file(path, mime_type="application/pdf")
            while f.state.name == "PROCESSING": time.sleep(1); f = genai.get_file(f.name)
            response = model.generate_content([f, prompt])
            return response.text
        except Exception as e: return f"שגיאה: {e}"

# --- 5. תצוגת תוכן ---
st.title("🏢 Apex Pro - דשבורד מפקח")

if full_path:
    st.success(f"נבחר דוח: {selected_file}")
    t1, t2, t3 = st.tabs(["📊 IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    with t1:
        if st.button("נתח CSM וחוזים מכבידים"):
            st.markdown(analyze(full_path, "נתח תנועת CSM וזהה חוזים מכבידים."))
            
    with t2:
        scen = st.selectbox("תרחיש:", ["רעידת אדמה", "עליית ריבית", "קריסת שווקים"])
        if st.button("הרץ סימולציה"):
            st.markdown(analyze(full_path, f"נתח השפעת {scen} על יחס סולבנסי."))

    with t3:
        st.info("בדיקת 5 מדדי ה-KPI הקריטיים מהזיכרון [cite: 2026-01-03]")
        if st.button("בצע ניתוח KPIs"):
            # שימוש במדדים ששמרנו בזיכרון [cite: 2026-01-03]
            p = "נתח: 1. יחס סולבנסי, 2. ROE, 3. Combined Ratio, 4. CSM, 5. נזילות." [cite: 2026-01-03]
            st.markdown(analyze(full_path, p))
else:
    st.info("👈 בחר דוח מהתפריט הימני כדי להתחיל.")
