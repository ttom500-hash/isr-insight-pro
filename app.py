import streamlit as st
import os

# 1. הגדרות דף ועיצוב יוקרתי (UI/UX)
st.set_page_config(page_title="Insurance Intelligence Pro", layout="wide")

# הזרקת סגנון נקי ומקצועי
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e1e4e8; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
""", unsafe_allow_html=True)

# 2. כותרת המערכת
st.title("🏛️ מערכת פיקוח הוליסטית - חברות ביטוח")
st.subheader("ניתוח דוחות כספיים ומדדי סולבנסי")

# 3. ניווט ובחירת נתונים (Sidebar)
with st.sidebar:
    st.image("https://www.gstatic.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png", width=100) # סמל זמני
    st.header("פרמטרים לסריקה")
    
    company = st.selectbox("בחר חברה:", ["Harel"])
    year = st.selectbox("שנה:", ["2025"])
    quarter = st.radio("רבעון דיווח:", ["Q1", "Q2", "Q3"])
    
    st.divider()
    
    # הגדרת נתיבי הקבצים לפי המבנה שבנינו בגיטהאב
    base_path = f"data/{company}/{year}/{quarter}"
    financial_file = f"{base_path}/financial/financial_report.pdf"
    solvency_file = f"{base_path}/solvency/solvency_report.pdf"
    
    st.info(f"מקור נתונים: {company} {year} {quarter}")

# 4. גוף האפליקציה - תצוגת הנתונים
tab1, tab2, tab3 = st.tabs(["📊 ניתוח פיננסי", "🛡️ יציבות (Solvency)", "📝 תובנות AI"])

with tab1:
    st.subheader(f"ניתוח דוח כספי - {company}")
    
    # בדיקת קיום קובץ בתיקייה
    if os.path.exists(financial_file):
        st.success(f"✅ הקובץ {os.path.basename(financial_file)} זוהה במערכת.")
    else:
        st.warning(f"🔎 ממתין לסנכרון קובץ בנתיב: {financial_file}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("רווח כולל", "₪---M", "ממתין לסריקה")
    with col2:
        st.metric("הון עצמי", "₪---B", "ממתין לסריקה")
    with col3:
        st.metric("ROE (משוער)", "---%", "ממתין לסריקה")

with tab2:
    st.subheader(f"מדדי יציבות - Solvency II")
    
    if os.path.exists(solvency_file):
        st.success(f"✅ קובץ סולבנסי זוהה: {os.path.basename(solvency_file)}")
    else:
        st.info("ℹ️ המערכת מוכנה לסריקת קובץ סולבנסי.")

    c1, c2 = st.columns(2)
    c1.metric("יחס סולבנסי", "---%", "ללא דגימה")
    c2.metric("הון נדרש (SCR)", "₪---M", "ללא דגימה")

with tab3:
    st.subheader("סיכום מנהלים (AI Generated)")
    st.write("כאן יוצגו 5 ה-KPI הקריטיים שביקשת לשמור לאחר חיבור ה-API Key.")
    st.code("Status: Waiting for Google Gemini API Connection...")

st.divider()
st.caption("מערכת תומכת החלטות למפקח | פותח עבור ניתוח חברות ביטוח 2026")
