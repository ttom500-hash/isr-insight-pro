import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור חכם (פותר שגיאת 404) ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

def get_api_key():
    if "GOOGLE_API_KEY" in st.secrets: return st.secrets["GOOGLE_API_KEY"]
    for key in st.secrets: return st.secrets[key]
    return None

api_key = get_api_key()
if not api_key:
    st.error("⛔ מפתח API לא נמצא.")
    st.stop()

genai.configure(api_key=api_key)

# פונקציה לבחירת מודל תקין אוטומטית
@st.cache_resource
def load_smart_model():
    try:
        # בדיקה אילו מודלים זמינים לחשבון שלך
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # עדיפות לגרסת ה-Flash המעודכנת
        model_name = next((m for m in available_models if "flash" in m), available_models[0])
        return genai.GenerativeModel(model_name)
    except:
        return genai.GenerativeModel("gemini-pro") # גיבוי למודל סטנדרטי

model = load_smart_model()

# --- 2. מנוע סריקת קבצים (ממלא את התפריט) ---
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

# --- 3. ממשק צד (ארכיון נתונים) ---
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
                selected_file = st.selectbox("דוח:", files)
                full_path = os.path.join(report_dir, selected_file)

# --- 4. לוגיקת ניתוח ---
def run_analysis(path, prompt):
    with st.spinner("מנתח..."):
        try:
            f = genai.upload_file(path, mime_type="application/pdf")
            while f.state.name == "PROCESSING":
                time.sleep(2)
                f = genai.get_file(f.name)
            response = model.generate_content([f, prompt])
            genai.delete_file(f.name)
            return response.text
        except Exception as e:
            return f"תקלה: {e}"

# --- 5. גוף האפליקציה ---
st.title("🏢 Apex Pro - דשבורד מפקח")

if full_path:
    st.success(f"נבחר דוח: {selected_file}")
    t1, t2, t3 = st.tabs(["📊 IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    with t1:
        if st.button("נתח CSM"):
            st.markdown(run_analysis(full_path, "נתח תנועת CSM וזהה חוזים מכבידים."))
            
    with t2:
        scen = st.selectbox("תרחיש:", ["רעידת אדמה", "עליית ריבית"])
        if st.button("הרץ סימולציה"):
            st.markdown(run_analysis(full_path, f"נתח השפעת {scen} על יחס סולבנסי."))

    with t3:
        st.info("בדיקת 5 מדדי ה-KPI הקריטיים [2026-01-03]")
        if st.button("בצע ניתוח KPIs מלא"):
            # שימוש ב-5 המדדים ששמרנו בזיכרון [cite: 2026-01-03]
            p = "נתח מהדוח: 1. יחס סולבנסי, 2. ROE (בהתבסס על רווח נקי), 3. Combined Ratio, 4. CSM, 5. נזילות." [cite: 2026-01-03]
            st.markdown(run_analysis(full_path, p))
else:
    st.info("👈 בחר דוח מהתפריט הימני.")
