import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# איתור מפתח API
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⛔ שגיאה קריטית: לא נמצא מפתח API ב-Secrets.")
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
            st.warning(f"נתיב לא נמצא: {report_dir}")
    else:
        st.error("לא נמצאו נתונים בתיקיית data. וודא שהמבנה ב-GitHub תקין.")

# --- 4. גוף האפליקציה (התוכן והניתוח) ---
st.title("🏢 Apex Pro - דשבורד אנליסט ומפקח")

if full_path:
    tab1, tab2, tab3 = st.tabs(["📊 ניתוח IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    with tab1:
        st.subheader("ניתוח עומק תקן IFRS 17")
        if st.button("נתח תנועת CSM"):
            st.info("מבצע ניתוח מודלים (GMM/VFA/PAA)...")
            # כאן תבוא פונקציית הניתוח המלאה של Gemini
            
    with tab2:
        st.subheader("סימולציית תרחישי קיצון")
        scenario = st.selectbox("בחר תרחיש:", ["רעידת אדמה", "עליית ריבית חדה", "קריסת שווקים"])
        if st.button("הרץ מבחן לחץ 🚀"):
            st.warning(f"מריץ סימולציה עבור תרחיש: {scenario}")

    with tab3:
        st.subheader("בדיקת 5 מדדי ה-KPI הקריטיים")
        st.info("בדיקה זו מבוססת על הצ'קליסט השמור בזיכרון המערכת.")
        if st.button("הפעל ניתוח KPIs סופי"):
            # פקודה מפורשת למודל להשתמש ב-5 המדדים ששמרנו
            prompt = "נתח את המדדים הבאים: 1. יחס סולבנסי, 2. ROE, 3. Combined Ratio, 4. תנועת CSM, 5. יחס נזילות."
            st.write("מנתח נתונים... אנא המתן.")
else:
    st.info("👈 אנא בחר דוח מהתפריט הימני כדי להתחיל.")
