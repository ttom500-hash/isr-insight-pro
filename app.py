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

# 2. פונקציית סריקה ישירה ל-v1 (מתוקנת)
def analyze_pdf_direct(file_path, api_key):
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    # פנייה מפורשת ל-v1 שעוקפת את כל הבעיות
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze this insurance report for Harel. Extract precisely: Net Profit, Total CSM balance, ROE, Gross Premiums, and Total Assets. Return only the values in Hebrew."},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }]
    }
    
    response = requests.post(url, json=payload)
    # תיקון שגיאת הכתיב כאן: status_code
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")

# 3. ממשק משתמש
st.title("🏛️ מערכת פיקוח הוליסטית - Apex Pro")
with st.sidebar:
    st.header("ניהול פיקוח")
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    api_key = st.secrets.get("GOOGLE_API_KEY")

tab1, tab2, tab3 = st.tabs(["📊 IFRS 17 ניתוח", "🛡️ סולבנסי", "🧪 סימולטור"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    # הצגת 5 מדדי ה-KPI מה-Saved Information שלך
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות ברוטו", "נכסים מנוהלים"]
    metrics_placeholders = [cols[i].empty() for i in range(5)]
    
    for i, label in enumerate(labels):
        metrics_placeholders[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת AI עמוקה"):
        if not api_key:
            st.error("Missing API Key!")
        elif os.path.exists(fin_path):
            with st.spinner("מנתח דוחות בנתיב v1 Stable..."):
                try:
                    result = analyze_pdf_direct(fin_path, api_key)
                    st.success("הסריקה הושלמה!")
                    st.markdown("### 🔍 ממצאי הניתוח:")
                    st.write(result)
                    st.balloons()
                except Exception as e:
                    st.error(f"שגיאה: {str(e)}")
        else:
            st.warning(f"קובץ חסר בנתיב: {fin_path}")

with tab2:
    st.subheader("מדדי Solvency II")
    st.metric("יחס סולבנסי משוער", "---%", "יעד: >100%")

st.divider()
st.caption("Apex Pro | 2026")
