import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות בסיס ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# ניסיון טעינת מפתח
try:
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("לא נמצא מפתח API ב-Secrets")
        st.stop()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error(f"שגיאת אתחול: {e}")
    st.stop()

# --- 2. מנוע סריקת קבצים ---
BASE_DIR = "data/Insurance_Warehouse"

def get_hierarchy():
    hierarchy = {}
    if os.path.exists(BASE_DIR):
        for company in os.listdir(BASE_DIR):
            c_path = os.path.join(BASE_DIR, company)
            if os.path.isdir(c_path):
                hierarchy[company] = {}
                for year in sorted(os.listdir(c_path), reverse=True):
                    y_path = os.path.join(c_path, year)
                    if os.path.isdir(y_path):
                        hierarchy[company][year] = ["Q1", "Q2", "Q3", "Q4"]
    return hierarchy

# --- 3. ממשק משתמש ---
st.title("🏢 Apex Pro - דשבורד מפקח")

with st.sidebar:
    st.header("📂 ארכיון נתונים")
    data_map = get_hierarchy()
    full_path = None
    if data_map:
        comp = st.selectbox("חברה:", list(data_map.keys()))
        year = st.selectbox("שנה:", list(data_map[comp].keys()))
        q = st.selectbox("רבעון:", data_map[comp][year])
        report_dir = os.path.join(BASE_DIR, comp, year, q, "Financial_Reports")
        if os.path.exists(report_dir):
            files = [f for f in os.listdir(report_dir) if f.endswith(".pdf")]
            if files:
                selected_file = st.selectbox("בחר דוח:", files)
                full_path = os.path.join(report_dir, selected_file)

# --- 4. ניתוח 5 המדדים הקריטיים ---
if full_path:
    st.success(f"נבחר דוח: {selected_file}")
    t1, t2, t3 = st.tabs(["📊 IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    with t3:
        st.info("ניתוח 5 המדדים הקריטיים מהצ'קליסט השמור [cite: 2026-01-03]")
        if st.button("בצע ניתוח KPIs"):
            with st.spinner("מנתח..."):
                try:
                    f = genai.upload_file(full_path, mime_type="application/pdf")
                    while f.state.name == "PROCESSING":
                        time.sleep(2)
                        f = genai.get_file(f.name)
                    
                    # פרומפט המבוסס על המדדים ששמרנו בזיכרון [cite: 2026-01-03]
                    p = "נתח מהדוח: 1. יחס סולבנסי, 2. ROE (בהתבסס על רווח נקי), 3. Combined Ratio, 4. CSM, 5. נזילות." [cite: 2026-01-03]
                    res = model.generate_content([f, p])
                    st.markdown(res.text)
                    
                    # מחיקת הקובץ מהשרת של גוגל בסיום לחיסכון במשאבים
                    genai.delete_file(f.name)
                except Exception as e:
                    st.error(f"תקלה בניתוח: {e}")
else:
    st.info("👈 בחר דוח מהתפריט הימני.")
