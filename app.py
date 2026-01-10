import streamlit as st
import google.generativeai as genai
from google.api_core import client_options
import os

# 1. שמירה על עיצוב Deep Navy (האפיון המקורי)
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. אתחול AI - הכרחת מעבר ל-v1 (פתרון ה-404 הסופי)
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        # הגדרת אפשרויות לקוח להכרחת v1
        opts = client_options.ClientOptions(api_endpoint="generativelanguage.googleapis.com")
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"], client_options=opts)
        
        # יצירת המודל - ה-SDK החדש יזהה את gemini-1.5-flash כמודל v1
        return genai.GenerativeModel('gemini-1.5-flash')
    return None

model = init_ai()

# 3. ממשק משתמש (Sidebar)
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
    
    # 5 מדדי ה-KPI מהאפיון המקורי
    cols = st.columns(5)
    for i, label in enumerate(["רווח כולל", "יתרת CSM", "ROE", "פרמיות", "נכסים"]):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת AI"):
        if model is None:
            st.error("Missing API Key!")
        elif os.path.exists(fin_path):
            with st.spinner("סורק דוחות בערוץ v1 היציב..."):
                try:
                    with open(fin_path, "rb") as f:
                        pdf_data = f.read()
                    
                    # קריאה למודל בפורמט הבסיסי ביותר
                    response = model.generate_content([
                        {"mime_type": "application/pdf", "data": pdf_data},
                        "Extract: Net Profit, Total CSM, and ROE. Hebrew results."
                    ])
                    
                    st.success("הסריקה הושלמה!")
                    st.markdown("### 🔍 ממצאים:")
                    st.write(response.text)
                    st.balloons()
                except Exception as e:
                    # הצגת השגיאה - אם עדיין כתוב v1beta, נצטרך פעולה ידנית ב-Streamlit
                    st.error(f"שגיאה בתקשורת: {str(e)}")
        else:
            st.warning(f"קובץ לא נמצא: {fin_path}")

st.divider()
st.caption("Apex Pro | 2026")
