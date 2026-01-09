import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור למנוע ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# משיכת המפתח מהסודות ששמרת
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⛔ שגיאה: לא נמצא מפתח API תקין ב-Secrets.")
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
                for year in os.listdir(c_path):
                    y_path = os.path.join(c_path, year)
                    if os.path.isdir(y_path):
                        hierarchy[company][year] = ["Q1", "Q2", "Q3", "Q4"]
    return hierarchy

# --- 3. ממשק צד (ניווט וחיפוש) ---
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
                selected_file = st.selectbox("בחר דוח לניתוח:", files)
                full_path = os.path.join(report_dir, selected_file)
            else:
                st.warning("אין קבצי PDF בתיקייה זו.")
        else:
            st.warning("לא נמצאו דוחות בנתיב זה.")
    else:
        st.error("לא נמצאו נתונים בתיקיית data. וודא שהמבנה ב-GitHub תקין.")

# --- 4. פונקציית ניתוח מול Gemini ---
def analyze_report(file_path, prompt_text):
    try:
        # העלאת הקובץ ל-Gemini
        uploaded_file = genai.upload_file(file_path, mime_type="application/pdf")
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(1)
            uploaded_file = genai.get_file(uploaded_file.name)
        
        # יצירת התשובה
        response = model.generate_content([uploaded_file, prompt_text])
        return response.text
    except Exception as e:
        return f"שגיאה בניתוח: {e}"

# --- 5. גוף האפליקציה (התוכן) ---
st.title("🏢 Apex Pro - דשבורד אנליסט ומפקח")

if full_path:
    st.success(f"נטען דוח: {selected_file}")
    tab1, tab2, tab3 = st.tabs(["📊 ניתוח IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    with tab1:
        st.subheader("ניתוח עומק תקן IFRS 17")
        if st.button("נתח תנועת CSM ומודלים"):
            res = analyze_report(full_path, "נתח את תנועת ה-CSM לפי מודלים (GMM, VFA, PAA) וזהה חוזים מכבידים.")
            st.markdown(res)
            
    with tab2:
        st.subheader("סימולציית תרחישי קיצון")
        scenario = st.selectbox("בחר תרחיש:", ["רעידת אדמה", "עליית ריבית חדה", "קריסת שווקים"])
        if st.button("הרץ מבחן לחץ 🚀"):
            res = analyze_report(full_path, f"נתח את השפעת תרחיש {scenario} על יחס הסולבנסי וההון העצמי.")
            st.markdown(res)

    with tab3:
        st.subheader("בדיקת 5 מדדי ה-KPI הקריטיים")
        st.info("בדיקה זו מבוססת על הצ'קליסט השמור בזיכרון המערכת.")
        if st.button("הפעל ניתוח KPIs סופי"):
            # שימוש ב-5 המדדים ששמרנו בזיכרון [cite: 2026-01-03]
            kpi_prompt = """
            נתח את 5 המדדים הבאים מהדוח:
            1. יחס כושר פירעון (Solvency Ratio) [cite: 2026-01-03].
            2. רווחיות להון (ROE) - השווה לרווח הנקי שראינו (למשל 246 מיליון ש"ח).
            3. Combined Ratio (יעילות חיתומית) [cite: 2026-01-03].
            4. תנועת CSM (צמיחת ערך עתידי) [cite: 2026-01-03].
            5. יחס נזילות (פירעון מיידי) [cite: 2026-01-03].
            """
            res = analyze_report(full_path, kpi_prompt)
            st.markdown(res)
else:
    st.info("👈 אנא בחר דוח מהתפריט הימני כדי להתחיל.")
