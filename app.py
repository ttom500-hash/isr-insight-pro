import streamlit as st
import requests
import base64
import os

# 1. עיצוב Deep Navy (נשמר בקפידה)
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. פונקציית סריקה עם המודל הכי יציב (Gemini Pro)
def analyze_pdf_direct(file_path, api_key):
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    # שימוש ב-gemini-pro - המודל הכי פחות רגיש לשגיאות 404
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # אם flash נכשל, נסה את הפניה הפשוטה ביותר לגרסה היציבה
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze this PDF. Extract: Net Profit, Total CSM, and ROE. Hebrew results."},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }]
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        # כאן נקבל את הודעת השגיאה המדויקת מהשרת
        return f"Error {response.status_code}: {response.text}"

# 3. ממשק משתמש
st.title("🏛️ Apex Pro - חדר בקרה מפקח")

with st.sidebar:
    st.header("הגדרות מערכת")
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ מפתח API חסר ב-Secrets!")
    else:
        st.success("מפתח API זוהה ✅")
    
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])

tab1, tab2 = st.tabs(["📊 ניתוח IFRS 17", "🛡️ יציבות הון"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    # 5 המדדים הקריטיים מהצ'קליסט שלך
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("רווח כולל", "₪---")
    c2.metric("יתרת CSM", "₪---")
    c3.metric("ROE", "---%")
    c4.metric("פרמיות ברוטו", "₪---")
    c5.metric("נכסים", "₪---")

    if st.button("🚀 הפעל סריקת עומק"):
        if os.path.exists(fin_path):
            with st.spinner("מנתח מסמך..."):
                res = analyze_pdf_direct(fin_path, api_key)
                st.markdown("### 🔍 ממצאי ה-AI:")
                st.write(res)
        else:
            st.error(f"קובץ לא נמצא בנתיב: {fin_path}")

st.divider()
st.caption("Apex Insurance Intelligence | 2026")
