import streamlit as st
import requests
import base64
import os
import time

# 1. עיצוב המערכת (Deep Navy)
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. פונקציית סריקה חכמה עם זיהוי עומס
def analyze_pdf_v1(file_path, api_key):
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
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
        return response.json()['candidates'][0]['content']['parts'][0]['text'], "success"
    elif response.status_code == 429:
        return "השרת עמוס (מכסת חינם). נא להמתין 60 שניות וללחוץ שוב על הכפתור.", "quota_error"
    else:
        return f"שגיאה {response.status_code}: {response.text}", "error"

# 3. ממשק משתמש
st.title("🏛️ חדר בקרה רגולטורי - Apex Pro")

api_key = st.secrets.get("GOOGLE_API_KEY")

with st.sidebar:
    st.header("סטטוס מערכת")
    if api_key:
        st.success("API Key מחובר ✅")
    company = st.selectbox("חברה", ["Harel"])
    st.info("מודל פעיל: Gemini 2.0 Flash")

tab1, tab2 = st.tabs(["📊 ניתוח IFRS 17", "🛡️ יציבות הון"])

with tab1:
    fin_path = f"data/{company}/2025/Q1/financial/financial_report.pdf"
    
    # תצוגת 5 מדדי ה-KPI מהאפיון המקורי
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות ברוטו", "נכסים"]
    for i, label in enumerate(labels):
        cols[i].metric(label, "₪---")

    st.divider()

    col_btn, col_diag = st.columns([1, 1])
    
    with col_btn:
        if st.button("🚀 הפעל סריקת עומק"):
            if os.path.exists(fin_path):
                with st.spinner("מנתח דוחות..."):
                    result, status = analyze_pdf_v1(fin_path, api_key)
                    if status == "success":
                        st.success("הסריקה הושלמה!")
                        st.write(result)
                        st.balloons()
                    elif status == "quota_error":
                        st.warning(result)
                    else:
                        st.error(result)
            else:
                st.error(f"קובץ לא נמצא: {fin_path}")

    with col_diag:
        if st.button("🧪 בדיקת מהירה (ללא קובץ)"):
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
            test_payload = {"contents": [{"parts": [{"text": "Respond with 'System Operational'"}]}]}
            test_res = requests.post(url, json=test_payload)
            if test_res.status_code == 200:
                st.write(f"תגובת AI: {test_res.json()['candidates'][0]['content']['parts'][0]['text']}")
            else:
                st.error(f"נכשל: {test_res.text}")

st.divider()
st.caption("Apex Pro - מערכת תומכת החלטות למפקח | 2026")
