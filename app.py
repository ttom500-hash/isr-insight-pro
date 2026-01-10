import streamlit as st
import google.generativeai as genai
import os

# 1. עיצוב ואיפיון (Deep Navy)
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    </style>
""", unsafe_allow_html=True)

# 2. אתחול AI - תיקון שורש הבעיה
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        # הגדרה מחדש של הקונפיגורציה
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # שימוש במודל ללא תחילית 'models/' כדי למנוע בלבול גרסאות
        return genai.GenerativeModel('gemini-1.5-flash')
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
    
    # תצוגת מדדים ריקים
    cols = st.columns(5)
    for i, label in enumerate(["רווח כולל", "יתרת CSM", "ROE", "פרמיות", "נכסים"]):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת AI"):
        if model is None:
            st.error("API Key missing!")
        elif os.path.exists(fin_path):
            with st.spinner("מנתח דוחות (v1 Stable)..."):
                try:
                    # קריאת הקובץ
                    with open(fin_path, "rb") as f:
                        pdf_data = f.read()
                    
                    # יצירת התוכן בפורמט פשוט שתואם v1
                    response = model.generate_content([
                        "Extract the following values from this document: Net Profit, Total CSM, and ROE. Return results in Hebrew.",
                        {"mime_type": "application/pdf", "data": pdf_data}
                    ])
                    
                    st.success("הסריקה הושלמה!")
                    st.markdown("### 🔍 ממצאים:")
                    st.write(response.text)
                    st.balloons()
                except Exception as e:
                    # כאן המערכת תציג את הודעת השגיאה המדויקת אם עדיין קיימת
                    st.error(f"שגיאה בתקשורת: {str(e)}")
        else:
            st.warning(f"קובץ לא נמצא בנתיב: {fin_path}")
