import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time
from datetime import datetime

# --- 1. הגדרות מערכת ועיצוב ---
st.set_page_config(page_title="Apex Pro Enterprise", page_icon="🏢", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700&display=swap');
    .stApp { direction: rtl; font-family: 'Heebo', sans-serif; text-align: right; }
    .methodology-box { background-color: #e3f2fd; border-right: 5px solid #2196f3; padding: 15px; border-radius: 5px; margin: 10px 0; }
    .alert-box { background-color: #ffebee; border-right: 5px solid #f44336; padding: 15px; border-radius: 5px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# --- 2. מנוע איתור מפתח (פותר את השגיאה הקריטית) ---
def get_api_key():
    # בודק את כל השמות האפשריים שסיפקת ב-Secrets
    return st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY") or st.secrets.get("A")

api_key = get_api_key()

if not api_key or api_key == "1": # בדיקה אם זה רק טקסט זמני
    st.error("⛔ שגיאה קריטית: לא נמצא מפתח API תקין ב-Secrets.")
    st.info("אנא ודא שב-Secrets מופיע: GOOGLE_API_KEY = 'המפתח_שלך'")
    st.stop()

genai.configure(api_key=api_key)

@st.cache_resource
def load_model():
    # איתור אוטומטי של המודל הזמין (Flash 1.5)
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        best_model = next((m for m in models if "flash" in m), models[0])
        return genai.GenerativeModel(best_model, system_instruction="אתה אקטואר ורגולטור ביטוח בכיר. נתח דוחות לפי IFRS 17 ו-Solvency II.")
    except:
        return genai.GenerativeModel("gemini-1.5-flash")

model = load_model()

# --- 3. 5 המדדים הקריטיים מהזיכרון ---
# מדדים אלו נשמרו בזיכרון המערכת לשימוש חוזר [cite: 2026-01-03]
KPI_PROMPT = """
נתח את 5 המדדים הקריטיים הבאים [cite: 2026-01-03]:
1. יחס כושר פירעון (Solvency Ratio) - השווה לדרישות ההון.
2. רווחיות להון (ROE) - נתח את איכות הרווח הנקי.
3. Combined Ratio - יעילות חיתומית.
4. מרווח CSM חדש - צמיחת ערך לפי IFRS 17.
5. יחס נזילות - יכולת פירעון מיידית.
עבור כל מדד: הצג מספר, מתודולוגיה, ודגלים אדומים 🚩.
"""

# --- 4. ממשק משתמש ---
with st.sidebar:
    st.title("📂 ארכיון נתונים")
    # לוגיקה לבחירת דוח (GitHub/Manual)
    # ... (כאן מגיע הקוד של בחירת הקבצים מה-Warehouse)

st.title("🏢 Apex Pro - דשבורד אנליסט ומפקח")

tab1, tab2, tab3, tab4 = st.tabs(["📊 ניתוח IFRS 17", "🌪️ תרחישי קיצון", "🏆 5 המדדים", "💬 צ'אט מומחה"])

with tab1:
    st.subheader("ניתוח עומק תקן IFRS 17")
    if st.button("נתח תנועת CSM ומודלים (GMM/VFA)"):
        # הפעלת ניתוח...
        pass

with tab2:
    st.subheader("סימולציית תרחישי קיצון (Solvency II)")
    scenario = st.selectbox("בחר תרחיש:", ["רעידת אדמה", "עליית ריבית חדה", "קריסת שווקים", "ביטולים המוניים"])
    if st.button("הרץ מבחן לחץ"):
        # הפעלת ניתוח...
        pass

with tab3:
    st.subheader("בדיקת 5 מדדי ה-KPI הקריטיים")
    st.info("בדיקה זו מבוססת על הצ'קליסט השמור בזיכרון האנליסט [cite: 2026-01-03].")
    if st.button("הפעל ניתוח KPIs"):
        # שימוש ב-KPI_PROMPT
        pass
