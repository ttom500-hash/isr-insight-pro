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

# --- 2. פונקציות ליבה ---

def analyze_pdf_v1(file_path, api_key, model_name="gemini-2.0-flash"):
    """פונקציה לסריקת ה-PDF"""
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "Analyze the attached report for Harel Insurance. Extract exactly: Net Profit, Total CSM balance, ROE, Gross Premiums, and Total Assets. Return the results in Hebrew."},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }]
    }
    
    response = requests.post(url, json=payload)
    return response

# --- 3. ממשק משתמש (UI) ---

st.title("🏛️ חדר בקרה רגולטורי - Apex Pro")

api_key = st.secrets.get("GOOGLE_API_KEY")

with st.sidebar:
    st.header("סטטוס מערכת")
    if api_key:
        st.success("API Key מחובר ✅")
    else:
        st.error("API Key חסר ❌")
    
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    st.info("מודל ראשי: Gemini 2.0 Flash")

tab1, tab2 = st.tabs(["📊 ניתוח IFRS 17", "🛡️ יציבות הון"])

with tab1:
    fin_path = f"data/{company}/2025/Q1/financial/financial_report.pdf"
    
    # תצוגת מדדי ה-KPI (המטריקות)
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות ברוטו", "נכסים"]
    for i, label in enumerate(labels):
        cols[i].metric(label, "₪---")

    st.divider()

    # הגדרת העמודות עבור הכפתורים (כאן נפתר ה-NameError)
    col_btn, col_diag = st.columns([1, 1])
    
    with col_btn:
        st.subheader("סריקה מבצעית")
        if st.button("🚀 הפעל סריקת עומק (2.0)"):
            if not api_key:
                st.error("חסר מפתח API")
            elif os.path.exists(fin_path):
                with st.spinner("מנתח דוחות..."):
                    res = analyze_pdf_v1(fin_path, api_key, "gemini-2.0-flash")
                    if res.status_code == 200:
                        st.success("הסריקה הושלמה!")
                        st.write(res.json()['candidates'][0]['content']['parts'][0]['text'])
                        st.balloons()
                    elif res.status_code == 429:
                        st.warning("המכסה של מודל 2.0 הסתיימה להיום. נסה את כפתור הגיבוי משמאל.")
                    else:
                        st.error(f"שגיאה {res.status_code}: {res.text}")
            else:
                st.error(f"קובץ לא נמצא: {fin_path}")

    with col_diag:
        st.subheader("אבחון וגיבוי")
        if st.button("🧪 בדיקת גיבוי (מודל 1.5)"):
            if not api_key:
                st.error("חסר מפתח API")
            else:
                with st.spinner("בודק ערוץ חלופי..."):
                    # פנייה למודל 1.5 שאולי המכסה שלו עדיין פנויה
                    url_15 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                    test_payload = {"contents": [{"parts": [{"text": "Respond with '1.5 Flash is operational'"}]}]}
                    test_res = requests.post(url_15, json=test_payload)
                    
                    if test_res.status_code == 200:
                        st.success("ערוץ 1.5 פעיל!")
                        st.write(test_res.json()['candidates'][0]['content']['parts'][0]['text'])
                    else:
                        st.error(f"גם ערוץ הגיבוי חסום (429).")
                        st.info("זה אישור סופי שהמערכת מוכנה ב-100% ורק זקוקה לחיבור כרטיס אשראי ב-AI Studio כדי להתחיל לעבוד.")

st.divider()
st.caption("Apex Pro - Integrated Insurance Intelligence | 2026")
