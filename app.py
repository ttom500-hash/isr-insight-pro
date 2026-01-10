import streamlit as st
import requests
import base64
import os

# --- 1. עיצוב המערכת (Deep Navy) ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. פונקציות אבחון ותקשורת ---
def get_available_models(api_key):
    """בודק איזה מודלים המפתח שלך באמת יכול לראות"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get('models', [])
        return [m['name'].split('/')[-1] for m in models if 'generateContent' in m['supportedGenerationMethods']]
    return []

def analyze_report(file_path, api_key, model_name):
    """ביצוע הסריקה בפועל"""
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze this insurance report. Extract: Net Profit, CSM, ROE. Hebrew results."},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }]
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    return f"שגיאה במודל {model_name}: {response.text}"

# --- 3. ממשק משתמש ---
st.title("🏛️ חדר בקרה - Apex Pro")

api_key = st.secrets.get("GOOGLE_API_KEY")

with st.sidebar:
    st.header("אבחון מערכת")
    if st.button("🔍 בדוק מודלים זמינים במפתח שלי"):
        if api_key:
            models = get_available_models(api_key)
            if models:
                st.write("מודלים שזמינים עבורך:")
                st.success(", ".join(models))
            else:
                st.error("המפתח שלך לא מורשה לאף מודל Gemini. צור מפתח חדש ב-AI Studio.")
        else:
            st.error("מפתח API לא הוגדר ב-Secrets.")

tab1, tab2 = st.tabs(["📊 IFRS 17 ניתוח", "🛡️ סולבנסי"])

with tab1:
    company = st.selectbox("חברה", ["Harel"])
    fin_path = f"data/{company}/2025/Q1/financial/financial_report.pdf"
    
    # 5 המדדים ששמרנו עבורך
    cols = st.columns(5)
    for i, label in enumerate(["רווח כולל", "יתרת CSM", "ROE", "פרמיות", "נכסים"]):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקה"):
        if os.path.exists(fin_path):
            with st.spinner("מנסה את המודל הטוב ביותר..."):
                # ניסיון אוטומטי לפי סדר עדיפויות
                success = False
                for m in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]:
                    result = analyze_report(fin_path, api_key, m)
                    if "Error" not in result and "שגיאה" not in result:
                        st.success(f"בוצע באמצעות: {m}")
                        st.write(result)
                        success = True
                        break
                if not success:
                    st.error("כל המודלים נחסמו. וודא שמפתח ה-API הופק ב-AI Studio.")
        else:
            st.error(f"קובץ חסר: {fin_path}")
