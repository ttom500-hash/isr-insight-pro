import streamlit as st
import google.generativeai as genai
import os

# 1. עיצוב ואיפיון (Deep Navy) - נשמר בדיוק כפי שביקשת
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. אתחול AI - שימוש בשם מודל ספציפי למניעת 404
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # שימוש בשם המודל המלא והמעודכן ביותר שעוקף את ה-v1beta
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    return None

model = init_ai()

# 3. ממשק משתמש
st.title("🏛️ מערכת פיקוח הוליסטית")
with st.sidebar:
    st.header("ניהול פיקוח")
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    st.caption(f"SDK Version: {genai.__version__}")

tab1, tab2 = st.tabs(["📊 IFRS 17 ניתוח", "🛡️ סולבנסי"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    # תצוגת מדדי ה-KPI מהאפיון המקורי
    cols = st.columns(5)
    for i, label in enumerate(["רווח כולל", "יתרת CSM", "ROE", "פרמיות", "נכסים"]):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת AI"):
        if model is None:
            st.error("Missing API Key!")
        elif os.path.exists(fin_path):
            with st.spinner("מנתח דוחות בגרסה יציבה (v1)..."):
                try:
                    # קריאת הקובץ
                    with open(fin_path, "rb") as f:
                        pdf_data = f.read()
                    
                    # שליחה בפורמט התואם ל-v1 Stable
                    response = model.generate_content([
                        {"mime_type": "application/pdf", "data": pdf_data},
                        "Extract the following values for Harel Q1 2025: Net Profit, Total CSM, and ROE. Return results in Hebrew."
                    ])
                    
                    st.success("הסריקה הושלמה בהצלחה!")
                    st.markdown("### 🔍 ממצאים:")
                    st.write(response.text)
                    st.balloons()
                except Exception as e:
                    # הצגת השגיאה בצורה ברורה לניפוי באגים
                    st.error(f"שגיאה בתקשורת: {str(e)}")
        else:
            st.warning(f"קובץ לא נמצא בנתיב: {fin_path}")

st.divider()
st.caption("Apex Pro - מערכת תומכת החלטות למפקח | 2026")
