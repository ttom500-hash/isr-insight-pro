import streamlit as st
import requests
import base64
import os

# 1. עיצוב ואיפיון (Deep Navy) - שמירה על כל הפיצ'רים שלך
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. פונקציית סריקה מותאמת למודל 2.0 (v1 Stable)
def analyze_pdf_v1(file_path, api_key):
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    # שימוש במודל gemini-2.0-flash שמופיע באבחון שלך כזמין ב-v1
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze the attached report for Harel Insurance. Extract exactly: Net Profit, Total CSM balance, ROE, Gross Premiums, and Total Assets. Return the results in Hebrew."},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }]
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")

# 3. ממשק משתמש
st.title("🏛️ מערכת פיקוח הוליסטית - Apex Pro")

with st.sidebar:
    st.header("הגדרות מערכת")
    api_key = st.secrets.get("GOOGLE_API_KEY")
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    st.caption(f"Active Model: gemini-2.0-flash")

tab1, tab2 = st.tabs(["📊 ניתוח IFRS 17", "🛡️ יציבות הון"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    # חמשת מדדי ה-KPI מהאפיון המקורי
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות ברוטו", "נכסים"]
    for i, label in enumerate(labels):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת עומק"):
        if not api_key:
            st.error("Missing API Key in Secrets!")
        elif os.path.exists(fin_path):
            with st.spinner("מנתח דוח פיננסי בערוץ v1 (דגם 2.0 Flash)..."):
                try:
                    result = analyze_pdf_v1(fin_path, api_key)
                    st.success("הסריקה הושלמה בהצלחה!")
                    st.markdown("### 🔍 ממצאי ה-AI:")
                    st.write(result)
                    st.balloons()
                except Exception as e:
                    st.error(f"שגיאה בתקשורת: {str(e)}")
        else:
            st.warning(f"קובץ לא נמצא בנתיב: {fin_path}")

st.divider()
st.caption("Apex Pro - ניתוח מבוסס v1 Stable (מודל 2.0) | 2026")
