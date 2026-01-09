import streamlit as st
import google.generativeai as genai
import os
import time

# --- הגדרות בסיס ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# משיכת המפתח החדש בלבד
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⛔ שגיאה: לא נמצא מפתח API ב-Secrets. אנא הוסף GOOGLE_API_KEY.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- מנוע היררכיית קבצים (ממלא את התפריט הריק) ---
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

# --- ממשק ניווט ---
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

# --- גוף האפליקציה ---
st.title("🏢 Apex Pro - דשבורד מפקח")

if full_path:
    st.success(f"נבחר דוח: {selected_file}")
    t1, t2, t3 = st.tabs(["📊 IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    # פונקציית ניתוח
    def run_analysis(p):
        with st.spinner("מנתח..."):
            try:
                f = genai.upload_file(full_path, mime_type="application/pdf")
                while f.state.name == "PROCESSING": time.sleep(1); f = genai.get_file(f.name)
                return model.generate_content([f, p]).text
            except Exception as e: return f"שגיאה: {e}"

    with t3:
        if st.button("בצע ניתוח KPIs מלא"):
            # שימוש ב-5 המדדים ששמרנו בזיכרון [cite: 2026-01-03]
            prompt = "נתח מהדוח: 1. יחס סולבנסי, 2. ROE, 3. Combined Ratio, 4. CSM, 5. נזילות."
            st.markdown(run_analysis(prompt))
else:
    st.info("👈 בחר דוח מהתפריט הימני כדי להתחיל.")
