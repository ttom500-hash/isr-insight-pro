import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# מנגנון איתור מפתח גמיש
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY") or st.secrets.get("A")

if not api_key:
    st.error("⛔ שגיאה: המפתח לא נמצא ב-Secrets. וודא שכתוב: GOOGLE_API_KEY = '...'")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- 2. מנוע סריקת קבצים ---
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
        year_list = sorted(list(data_map[comp].keys()), reverse=True)
        year = st.selectbox("בחר שנה:", year_list)
        q = st.selectbox("בחר רבעון:", data_map[comp][year])
        
        report_dir = os.path.join(BASE_DIR, comp, year, q, "Financial_Reports")
        if os.path.exists(report_dir):
            files = [f for f in os.listdir(report_dir) if f.endswith(".pdf")]
            if files:
                selected_file = st.selectbox("בחר דוח:", files)
                full_path = os.path.join(report_dir, selected_file)
            else:
                st.warning("לא נמצאו קבצי PDF בתיקייה.")
        else:
            st.warning("נתיב הדוחות לא נמצא.")
    else:
        st.error("תיקיית data לא נמצאה ב-GitHub.")

# --- 4. פונקציית ניתוח ---
def analyze(path, prompt_text):
    with st.spinner("מנתח נתונים ברמה אקטוארית..."):
        try:
            f = genai.upload_file(path, mime_type="application/pdf")
            while f.state.name == "PROCESSING":
                time.sleep(1)
                f = genai.get_file(f.name)
            response = model.generate_content([f, prompt_text])
            return response.text
        except Exception as e:
            return f"שגיאה בתהליך הניתוח: {e}"

# --- 5. גוף האפליקציה ---
st.title("🏢 Apex Pro - דשבורד מפקח")

if full_path:
    st.success(f"נבחר דוח: {selected_file}")
    t1, t2, t3 = st.tabs(["📊 IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    with t1:
        st.subheader("ניתוח תקן IFRS 17")
        if st.button("נתח תנועת CSM וחוזים מכבידים"):
            res = analyze(full_path, "בצע ניתוח עומק של תנועת ה-CSM וזהה חוזים מכבידים במגזרי הפעילות.")
            st.markdown(res)
            
    with t2:
        st.subheader("מבחני לחץ (Solvency II)")
        scen = st.selectbox("בחר תרחיש קיצון:", ["רעידת אדמה", "עליית ריבית", "קריסת שווקים"])
        if st.button("הרץ סימולציה 🚀"):
            res = analyze(full_path, f"נתח את השפעת תרחיש {scen} על יחס כושר הפירעון (Solvency Ratio).")
            st.markdown(res)

    with t3:
        st.subheader("5 המדדים הקריטיים (KPIs)")
        st.info("ניתוח אוטומטי המבוסס על צ'קליסט הזיכרון של המערכת.")
        if st.button("בצע ניתוח KPIs מלא"):
            # פקודה מפורשת לניתוח 5 המדדים ששמרנו בזיכרון [cite: 2026-01-03]
            p = "נתח את המדדים הבאים מהדוח: 1. יחס סולבנסי, 2. ROE, 3. Combined Ratio, 4. תנועת CSM, 5. יחס נזילות."
            res = analyze(full_path, p)
            st.markdown(res)
else:
    st.info("👈 בחר דוח מהתפריט הימני (ארכיון הנתונים) כדי להתחיל בניתוח.")
