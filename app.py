import streamlit as st
import google.generativeai as genai
import os

# 1. הגדרות דף וחיבור ל-AI
st.set_page_config(page_title="Insurance AI Monitor", layout="wide")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing API Key in Secrets!")

# 2. כותרת
st.title("🏛️ מערכת פיקוח הוליסטית - חברות ביטוח")

# 3. ניווט
with st.sidebar:
    st.header("🔍 בחירת דוח")
    company = st.selectbox("חברה", ["Harel"])
    year = st.selectbox("שנה", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    st.divider()
    # נתיבים לקבצים
    fin_path = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    sol_path = f"data/{company}/{year}/{quarter}/solvency/solvency_report.pdf"

# 4. תצוגה
tab1, tab2 = st.tabs(["📊 ניתוח פיננסי", "🛡️ מדדי יציבות"])

with tab1:
    st.subheader(f"ניתוח {company} - {quarter}/{year}")
    
    if os.path.exists(fin_path):
        st.success(f"✅ קובץ מזוהה: {os.path.basename(fin_path)}")
        
        if st.button("🚀 הפעל סריקת 5 מדדי KPI קריטיים"):
            with st.spinner("ה-AI קורא את ה-PDF..."):
                # כאן המערכת תבצע את השליפה האמיתית ברגע שנחבר את פונקציית הקריאה
                st.info("📊 5 המדדים שנשמרו בניתוח:")
                cols = st.columns(5)
                cols[0].metric("רווח כולל", "₪---M")
                cols[1].metric("הון עצמי", "₪---B")
                cols[2].metric("ROE", "---%")
                cols[3].metric("CSM", "₪---B")
                cols[4].metric("פרמיות", "₪---M")
    else:
        st.warning(f"קובץ לא נמצא בנתיב: {fin_path}")

with tab2:
    st.subheader("מדדי סולבנסי")
    if os.path.exists(sol_path):
        st.metric("יחס סולבנסי (משוער)", "---%", "ממתין לסריקה")
    else:
        st.info("העלה דוח סולבנסי כדי לראות נתונים כאן.")
