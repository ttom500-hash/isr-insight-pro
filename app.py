import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

def get_api_key():
    if "GOOGLE_API_KEY" in st.secrets: return st.secrets["GOOGLE_API_KEY"]
    for key in st.secrets: return st.secrets[key]
    return None

api_key = get_api_key()
if not api_key:
    st.error("לא נמצא מפתח API.")
    st.stop()

genai.configure(api_key=api_key)

@st.cache_resource
def load_smart_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if "flash" in m), available_models[0])
        return genai.GenerativeModel(model_name)
    except:
        return genai.GenerativeModel("gemini-1.5-flash")

model = load_smart_model()

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

# --- 4. ניתוח דוחות ---
if full_path:
    st.success(f"נבחר דוח: {selected_file}")
    t1, t2, t3 = st.tabs(["📊 IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    def run_analysis(p):
        with st.spinner("מנתח נתונים..."):
            try:
                f = genai.upload_file(full_path, mime_type="application/pdf")
                while f.state.name == "PROCESSING":
                    time.sleep(2)
                    f = genai.get_file(f.name)
                response = model.generate_content([f, p])
                genai.delete_file(f.name)
                return response.text
            except Exception as e:
                return f"תקלה: {e}"

    with t3:
        st.info("ניתוח 5 המדדים הקריטיים מהצ'קליסט השמור")
        if st.button("בצע ניתוח KPIs מלא"):
            # פקודה לניתוח 5 המדדים ששמרנו בזיכרון
            prompt = "נתח מהדוח: 1. יחס סולבנסי, 2. ROE (בהתבסס על רווח נקי), 3. Combined Ratio, 4. CSM, 5. נזילות."
            st.markdown(run_analysis(prompt))
else:
    st.info("👈 בחר דוח מהתפריט הימני.")
