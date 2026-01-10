import streamlit as st
import google.generativeai as genai
import requests
import base64
import os

# 1. שמירה על האפיון המקורי (Deep Navy)
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. פונקציית סריקה ישירה (Direct v1 Call) - פותר את ה-404 סופית
def analyze_pdf_direct(file_path, api_key):
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    # פנייה ישירה ל-v1 (ולא ל-v1beta)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze this insurance financial report. Extract: Net Profit, Total CSM balance, and ROE. Return results in Hebrew."},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }]
    }
    
    response = requests.post(url, json=payload)
    if response.status_status == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")

# 3. ממשק משתמש
st.title("🏛️ מערכת פיקוח הוליסטית")
with st.sidebar:
    st.header("ניהול פיקוח")
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    api_key = st.secrets.get("GOOGLE_API_KEY")

tab1, tab2 = st.tabs(["📊 IFRS 17 ניתוח", "🛡️ סולבנסי"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    # 5 מדדי ה-KPI מהאפיון המקורי (השתמשנו ב-Saved Info שלך)
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות ברוטו", "נכסים מנוהלים"]
    for i, label in enumerate(labels):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת AI עמוקה"):
        if not api_key:
            st.error("Missing API Key in Secrets!")
        elif os.path.exists(fin_path):
            with st.spinner("מבצע מעקף SDK ופנייה ישירה ל-v1 Stable..."):
                try:
                    result = analyze_pdf_direct(fin_path, api_key)
                    st.success("הסריקה הושלמה בהצלחה!")
                    st.markdown("### 🔍 ממצאי הניתוח (IFRS 17):")
                    st.write(result)
                    st.balloons()
                except Exception as e:
                    st.error(f"שגיאה סופית: {str(e)}")
        else:
            st.warning(f"קובץ חסר: {fin_path}")

st.divider()
st.caption("Apex Pro - ניתוח מבוסס v1 Stable | 2026")
