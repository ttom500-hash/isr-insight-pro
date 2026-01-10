import streamlit as st
import requests
import base64
import os

# 1. עיצוב Deep Navy (האפיון המקורי)
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. פונקציית סריקה עם המודל הכי זמין (Static Version)
def analyze_pdf_direct(file_path, api_key):
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    # שימוש בגרסה הסטטית 8b - היא הזמינה ביותר גלובלית
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze the attached financial report for Harel Insurance. Extract exactly: Net Profit, Total CSM balance, ROE, Gross Premiums, and Total Assets. Return the results in Hebrew."},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }]
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        # כאן נקבל פירוט אם גם זה נכשל
        raise Exception(f"API Error {response.status_code}: {response.text}")

# 3. ממשק משתמש
st.title("🏛️ מערכת פיקוח הוליסטית - Apex Pro")

with st.sidebar:
    st.header("ניהול פיקוח")
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    api_key = st.secrets.get("GOOGLE_API_KEY")

tab1, tab2 = st.tabs(["📊 IFRS 17 ניתוח", "🛡️ סולבנסי"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    # הצגת 5 מדדי ה-KPI לפי הצ'קליסט ששמרנו עבורך
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות ברוטו", "נכסים מנוהלים"]
    for i, label in enumerate(labels):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת AI"):
        if not api_key:
            st.error("Missing API Key! Please add GOOGLE_API_KEY to Streamlit Secrets.")
        elif os.path.exists(fin_path):
            with st.spinner("סורק דוחות בעזרת Gemini 1.5 Flash 8B..."):
                try:
                    result = analyze_pdf_direct(fin_path, api_key)
                    st.success("הסריקה הושלמה!")
                    st.markdown("### 🔍 ממצאי הניתוח:")
                    st.write(result)
                    st.balloons()
                except Exception as e:
                    st.error(f"שגיאה: {str(e)}")
                    st.info("אם מופיע 404, בדוק אם המפתח שלך פעיל ב-Google AI Studio.")
        else:
            st.warning(f"קובץ לא נמצא בנתיב: {fin_path}")

st.divider()
st.caption("Apex Pro - ניתוח פיננסי מתקדם | 2026")
