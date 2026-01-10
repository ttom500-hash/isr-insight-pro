import streamlit as st
import google.generativeai as genai
import os

# 1. עיצוב ואיפיון
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""<style>.main { background-color: #0e1117; color: white; } .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }</style>""", unsafe_allow_html=True)

# 2. אתחול AI עם בדיקת גרסה
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # הדפסת גרסת ה-SDK ללוגים
        print(f"DEBUG: Running with SDK Version: {genai.__version__}")
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

tab1, tab2 = st.tabs(["📊 IFRS 17", "🛡️ סולבנסי"])

with tab1:
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות", "נכסים"]
    for i, label in enumerate(labels): cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת AI"):
        if os.path.exists(fin_path):
            with st.spinner("מנתח בגרסת v1 Stable..."):
                try:
                    with open(fin_path, "rb") as f:
                        pdf_data = f.read()
                    # פנייה מפורשת למודל יציב
                    response = model.generate_content([
                        {"mime_type": "application/pdf", "data": pdf_data},
                        "Extract: Net Profit, CSM, ROE. Hebrew results."
                    ])
                    st.write(response.text)
                except Exception as e:
                    st.error(f"שגיאה: {str(e)}")
        else:
            st.warning(f"קובץ חסר: {fin_path}")
