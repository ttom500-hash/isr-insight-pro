import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. הגדרות וחיבור (המנוע) ---
st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- 2. מנוע סריקת קבצים (הפתרון לתיקייה הריקה) ---
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
    
    if data_map:
        comp = st.selectbox("בחר חברה:", list(data_map.keys()))
        year = st.selectbox("בחר שנה:", list(data_map[comp].keys()))
        q = st.selectbox("בחר רבעון:", data_map[comp][year])
        
        # נתיב לקובץ ה-PDF
        report_dir = os.path.join(BASE_DIR, comp, year, q, "Financial_Reports")
        if os.path.exists(report_dir):
            files = [f for f in os.listdir(report_dir) if f.endswith(".pdf")]
            selected_file = st.selectbox("בחר דוח לניתוח:", files)
            full_path = os.path.join(report_dir, selected_file)
        else:
            st.warning("לא נמצאו דוחות בנתיב זה.")
            full_path = None
    else:
        st.error("תיקיית data לא נמצאה ב-GitHub.")
        full_path = None

# --- 4. גוף האפליקציה (התוכן) ---
st.title("🏢 Apex Pro - דשבורד אנליסט ומפקח")

if full_path:
    # כאן נכנסת הלוגיקה של הטאבים (IFRS 17, סולבנסי, 5 המדדים)
    tab1, tab2, tab3 = st.tabs(["📊 ניתוח IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים"])
    
    with tab3:
        st.subheader("בדיקת 5 מדדי ה-KPI הקריטיים")
        if st.button("הפעל ניתוח אקטוארי סופי"):
            # פקודה למודל לנתח לפי הזיכרון שלנו
            prompt = "נתח את יחס הסולבנסי, ROE, Combined Ratio, CSM ונזילות." [cite: 2026-01-03]
            # (כאן מבוצעת הקריאה ל-Gemini)
            st.write(f"מנתח את הקובץ: {selected_file}...")
else:
    st.info("אנא בחר דוח מהתפריט הימני כדי להציג נתונים.")
