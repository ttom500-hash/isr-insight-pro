import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור גמיש למפתח ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# מנגנון איתור מפתח גמיש - מחפש את השם המדויק או כל ערך קיים
def get_api_key():
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    # אם המשתמש קרא למפתח בשם אחר, ננסה למשוך את הערך הראשון שנמצא
    for key in st.secrets:
        return st.secrets[key]
    return None

api_key = get_api_key()

if not api_key:
    st.error("⛔ שגיאה: לא נמצא מפתח API ב-Secrets. אנא הוסף אותו בהגדרות האפליקציה.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- 2. מנוע סריקת קבצים (ממלא את התפריט הימני) ---
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

# --- 3. ממשק צד (ניווט) ---
with st.sidebar:
    st.header("📂 ארכיון נתונים")
    data_map = get_hierarchy()
    full_path = None
    if data_map:
        comp = st.selectbox("בחר חברה:", list(data_map.keys()))
        year = st.selectbox("בחר שנה:", list(data_map[comp].keys()))
        q = st.selectbox("בחר רבעון:", data_map[comp][year])
        report_dir = os.path.join(BASE_DIR, comp, year, q, "Financial_Reports")
        if os.path.exists(report_dir):
            files = [f for f in os.listdir(report_dir) if f.endswith(".pdf")]
            if files:
                selected_file = st.selectbox("בחר דוח:", files)
                full_path = os.path.join(report_dir, selected_file)
    else:
        st.error("תיקיית data לא נמצאה ב-GitHub.")

# --- 4. פונקציית הניתוח ---
def run_analysis(path, prompt):
    with st.spinner("מנתח נתונים..."):
        try:
            f = genai.upload_file(path, mime_type="application/pdf")
            while f.state.name == "PROCESSING":
                time.sleep(2)
                f = genai.get_file(f.name)
            response = model.generate_content([f, prompt])
            genai.delete_file(f.name) # ניקוי בסיום
            return response.text
        except Exception as e:
            return f"תקלה בניתוח: {e}"

# --- 5. גוף האפליקציה (התוכן) ---
st.title("🏢 Apex Pro - דשבורד מפקח")

if full_path:
    st.success(f"נבחר דוח: {selected_file}")
    t1, t2, t3 = st.tabs(["📊 IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    with t1:
        st.subheader("ניתוח תקן IFRS 17")
        if st.button("נתח תנועת CSM"):
            res = run_analysis(full_path, "בצע ניתוח עומק של תנועת ה-CSM וזהה חוזים מכבידים.")
            st.markdown(res)
            
    with t2:
        st.subheader("מבחני לחץ")
        scen = st.selectbox("בחר תרחיש:", ["רעידת אדמה", "עליית ריבית", "קריסת שווקים"])
        if st.button("הרץ סימולציה 🚀"):
            res = run_analysis(full_path, f"נתח את השפעת תרחיש {scen} על יחס הסולבנסי.")
            st.markdown(res)

    with t3:
        st.subheader("5 המדדים הקריטיים (KPIs)")
        st.info("ניתוח המבוסס על צ'קליסט הזיכרון [2026-01-03]")
        if st.button("בצע ניתוח KPIs מלא"):
            # שימוש ב-5 המדדים ששמרנו בזיכרון
            p = "נתח מהדוח: 1. יחס סולבנסי, 2. ROE (על בסיס רווח נקי), 3. Combined Ratio, 4. CSM, 5. נזילות."
            st.markdown(run_analysis(full_path, p))
else:
    st.info("👈 בחר דוח מהתפריט הימני כדי להתחיל.")
