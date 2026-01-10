import streamlit as st
import requests
import base64
import os

# --- 1. עיצוב וסגנון ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. פונקציית הליבה: ניתוח עם גיבוי (Fallback) ---
def analyze_pdf(file_path, api_key):
    with open(file_path, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # רשימת מודלים לניסיון בסדר עדיפות
    models_to_try = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
    
    last_error = ""
    for model_name in models_to_try:
        # שימוש ב-v1beta - הנתיב הכי בטוח למניעת 404 ב-2026
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Analyze this report for Harel Insurance. Extract: Net Profit, Total CSM, ROE, Gross Premiums, Total Assets. Hebrew results."},
                    {"inline_data": {"mime_type": "application/pdf", "data": pdf_base64}}
                ]
            }]
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text'], model_name
            else:
                last_error = response.text
                continue # נסיון המודל הבא ברשימה
        except Exception as e:
            last_error = str(e)
            continue

    raise Exception(f"כל המודלים נכשלו. שגיאה אחרונה: {last_error}")

# --- 3. ממשק משתמש ---
st.title("🏛️ Apex Pro - מערכת פיקוח חכמה")

with st.sidebar:
    st.header("ניהול והגדרות")
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if api_key:
        st.success("API Key מחובר ✅")
    
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    
    # כפתור אבחון למקרה של תקלות
    if st.button("🔍 אבחון זמינות מודלים"):
        diag_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        diag_res = requests.get(diag_url)
        st.write(diag_res.json())

tab1, tab2 = st.tabs(["📊 ניתוח פיננסי", "🛡️ סולבנסי"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    # תצוגת 5 המדדים ששמרנו באפיון
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות ברוטו", "נכסים"]
    for i, label in enumerate(labels):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקה חסינת כשל"):
        if not api_key:
            st.error("API Key missing in Secrets!")
        elif os.path.exists(fin_path):
            with st.spinner("מנסה להתחבר למודל הפנוי ביותר..."):
                try:
                    text_result, used_model = analyze_pdf(fin_path, api_key)
                    st.success(f"הסריקה הושלמה באמצעות {used_model}!")
                    st.markdown("### 🔍 ממצאי ה-AI:")
                    st.write(text_result)
                    st.balloons()
                except Exception as e:
                    st.error(f"שגיאה קריטית: {str(e)}")
        else:
            st.warning(f"קובץ חסר בנתיב: {fin_path}")

st.divider()
st.caption("Apex Pro - Integrated Insurance Intelligence | 2026")
