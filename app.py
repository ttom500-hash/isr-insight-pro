import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# משיכת מפתח API מה-Secrets
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⛔ שגיאה: לא נמצא מפתח API ב-Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# מנגנון בחירת מודל אוטומטי למניעת שגיאת 404
@st.cache_resource
def get_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # מחפש עדיפות ל-Flash
        selected = next((m for m in models if "1.5-flash" in m), models[0])
        return genai.GenerativeModel(selected)
    except Exception as e:
        st.error(f"תקלה בגישה למודלים: {e}")
        st.stop()

model = get_model()

# --- 2. מנוע סריקת קבצים (הפתרון ל'אין כלום') ---
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

# --- 3. ממשק ניווט ---
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
    else:
        st.error("לא נמצאה תיקיית data ב-GitHub.")

# --- 4. גוף האפליקציה ---
st.title("🏢 Apex Pro - דשבורד מפקח")

if full_path:
    st.success(f"נבחר דוח: {selected_file}")
    t1, t2, t3 = st.tabs(["📊 IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    def run_analysis(p):
        with st.spinner("מנתח..."):
            try:
                f = genai.upload_file(full_path, mime_type="application/pdf")
                while f.state.name == "PROCESSING": time.sleep(1); f = genai.get_file(f.name)
                return model.generate_content([f, p]).text
            except Exception as e: return f"שגיאה: {e}"

    with t3:
        st.info("ניתוח 5 המדדים הקריטיים (KPIs) השמורים בזיכרון")
        if st.button("בצע ניתוח KPIs מלא"):
            # שימוש במדדים ששמרנו בזיכרון
            prompt = "נתח מהדוח: 1. יחס סולבנסי, 2. ROE, 3. Combined Ratio, 4. CSM, 5. נזילות."
            st.markdown(run_analysis(prompt))
else:
    st.info("👈 בחר דוח מהתפריט הימני כדי להתחיל.")
