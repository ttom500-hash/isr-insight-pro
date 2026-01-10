import streamlit as st
import google.generativeai as genai
import os

# 1. הגדרות דף ועיצוב
st.set_page_config(page_title="Insurance Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e1e4e8; }
    </style>
""", unsafe_allow_html=True)

# 2. פונקציית עזר לשליפת ה-API Key
def get_api_key():
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    return None

# 3. כותרת המערכת
st.title("🏛️ מערכת פיקוח הוליסטית - חברות ביטוח")

# 4. ניווט (Sidebar)
with st.sidebar:
    st.header("פרמטרים לסריקה")
    company = st.selectbox("בחר חברה:", ["Harel"])
    year = st.selectbox("שנה:", ["2025"])
    quarter = st.radio("רבעון דיווח:", ["Q1", "Q2", "Q3"])
    
    st.divider()
    base_path = f"data/{company}/{year}/{quarter}"
    financial_file = f"{base_path}/financial/financial_report.pdf"
    solvency_file = f"{base_path}/solvency/solvency_report.pdf"
    
    api_key = get_api_key()
    if api_key:
        st.success("AI Engine: Connected ✅")
    else:
        st.error("AI Engine: Disconnected ❌")

# 5. גוף האפליקציה
tab1, tab2, tab3 = st.tabs(["📊 ניתוח פיננסי", "🛡️ יציבות (Solvency)", "📝 תובנות AI"])

with tab1:
    st.subheader(f"ניתוח דוח כספי - {company}")
    if os.path.exists(financial_file):
        st.success(f"✅ זוהה במערכת הקובץ: {os.path.basename(financial_file)}")
        col1, col2, col3 = st.columns(3)
        col1.metric("רווח כולל", "₪---M", "ממתין לסריקה")
        col2.metric("הון עצמי", "₪---B", "ממתין לסריקה")
        col3.metric("ROE (משוער)", "---%", "ממתין לסריקה")
    else:
        st.warning(f"🔎 קובץ לא נמצא בנתיב: {financial_file}")

with tab2:
    st.subheader(f"מדדי יציבות - Solvency II")
    if os.path.exists(solvency_file):
        st.success(f"✅ זוהה במערכת הקובץ: {os.path.basename(solvency_file)}")
        c1, c2 = st.columns(2)
        c1.metric("יחס סולבנסי", "---%", "ממתין")
        c2.metric("הון נדרש (SCR)", "₪---M", "ממתין")
    else:
        st.info(f"ממתין להעלאת קובץ סולבנסי בנתיב: {solvency_file}")

with tab3:
    st.subheader("ניתוח חכם (AI Insights)")
    if not api_key:
        st.warning("אנא הגדר את ה-GOOGLE_API_KEY ב-Secrets של Streamlit כדי להפעיל את הניתוח.")
    else:
        st.info("מנוע ה-AI מוכן לניתוח 5 מדדי ה-KPI הקריטיים.")

st.divider()
st.caption("מערכת תומכת החלטות למפקח | Insurance Intelligence App 2026")
