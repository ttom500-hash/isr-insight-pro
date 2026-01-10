import streamlit as st
import google.generativeai as genai
from google.generativeai.types import RequestOptions
import os

# 1. עיצוב ואיפיון (Deep Navy) - שמירה קפדנית על העיצוב שלך
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# 2. אתחול AI - הכרחת שימוש ב-v1
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # יצירת מודל עם הגדרה מפורשת לגרסה v1
        return genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            # פתרון ה-404: עקיפת ה-beta דרך RequestOptions
        )
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
    
    # תצוגת 5 המדדים מהאפיון המקורי
    cols = st.columns(5)
    labels = ["רווח כולל", "יתרת CSM", "ROE", "פרמיות", "נכסים"]
    for i, label in enumerate(labels):
        cols[i].metric(label, "₪---")

    if st.button("🚀 הפעל סריקת AI"):
        if model is None:
            st.error("Missing API Key!")
        elif os.path.exists(fin_path):
            with st.spinner("מנתח דוחות בנתיב v1 Stable..."):
                try:
                    with open(fin_path, "rb") as f:
                        pdf_data = f.read()
                    
                    # שימוש ב-RequestOptions כדי להכריח את ה-API להשתמש ב-v1
                    response = model.generate_content(
                        [
                            {"mime_type": "application/pdf", "data": pdf_data},
                            "נתח את הדוח הכספי ושלוף: רווח נקי, יתרת CSM ותשואה להון (ROE). החזר תוצאות בעברית."
                        ],
                        request_options=RequestOptions(api_version='v1')
                    )
                    
                    st.success("הסריקה הושלמה!")
                    st.markdown("### 🔍 ממצאים:")
                    st.write(response.text)
                    st.balloons()
                except Exception as e:
                    st.error(f"שגיאה בתקשורת: {str(e)}")
        else:
            st.warning(f"קובץ חסר בנתיב: {fin_path}")

st.divider()
st.caption("Apex Pro | 2026")
