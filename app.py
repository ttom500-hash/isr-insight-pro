import streamlit as st
import requests
import base64
import os

# --- 1. הגדרות עיצוב (Deep Navy) ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. פונקציית סריקה ישירה (עוקפת SDK) ---
def analyze_pdf_direct(file_path, api_key):
    # קריאת הקובץ והמרה ל-Base64
    with open(file_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    # כתובת ה-API הישירה למודל Pro בגרסה היציבה v1
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={api_key}"
    
    # גוף הבקשה
    payload = {
        "contents": [{
            "parts": [
                {"text": "You are an expert insurance regulator. Analyze the attached financial report for Harel Insurance. Extract exactly these 5 KPIs: 1. Net Profit, 2. Total CSM balance, 3. ROE, 4. Gross Premiums, 5. Total Assets. Return the results in Hebrew."},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }]
    }
    
    # שליחת הבקשה
    response = requests.post(url, json=payload)
    
    # בדיקת תקינות
    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except KeyError:
            return "התקבל פלט לא תקין מהמודל (מבנה JSON לא צפוי)."
    else:
        # החזרת שגיאה מפורטת במקרה של כישלון
        error_msg = response.json().get('error', {}).get('message', response.text)
        raise Exception(f"API Error {response.status_code}: {error_msg}")

# --- 3. ממשק המשתמש ---
st.title("🏛️ מערכת פיקוח הוליסטית - Apex Pro")

# סרגל צד
with st.sidebar:
    st.header("ניהול פיקוח")
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    
    # שליפת המפתח מה-Secrets
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if api_key:
        st.success("API Key מחובר ✅")
    else:
        st.error("חסר מפתח API ב-Secrets ❌")

# גוף המערכת - טאבים
tab1, tab2, tab3 = st.tabs(["📊 IFRS 17 ניתוח", "🛡️ סולבנסי", "🧪 סימולטור"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    # תצוגת 5 המדדים (KPIs)
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות ברוטו", "נכסים מנוהלים"]
    for i, label in enumerate(labels):
        cols[i].metric(label, "₪---")

    st.markdown("---")
    
    # כפתור הפעלה
    if st.button("🚀 הפעל סריקת AI עמוקה (Pro)"):
        if not api_key:
            st.error("נא להגדיר GOOGLE_API_KEY ב-Secrets של האפליקציה.")
        elif not os.path.exists(fin_path):
            st.warning(f"לא נמצא קובץ PDF בנתיב: {fin_path}")
        else:
            with st.spinner("מנתח דוחות באמצעות Gemini 1.5 Pro..."):
                try:
                    # הפעלת הפונקציה הישירה
                    result = analyze_pdf_direct(fin_path, api_key)
                    
                    st.success("הניתוח הושלם בהצלחה!")
                    st.markdown("### 🔍 ממצאי הניתוח:")
                    st.write(result)
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"שגיאה בתקשורת עם ה-AI: {str(e)}")

with tab2:
    st.subheader("מדדי Solvency II")
    st.metric("יחס סולבנסי משוער", "---%", "יעד: >100%")

st.divider()
st.caption("Apex Pro - מנוע Gemini 1.5 Pro | 2026")
