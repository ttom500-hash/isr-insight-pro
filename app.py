import streamlit as st
import google.generativeai as genai
import os

# --- 1. הגדרות דף ועיצוב יוקרתי (Deep Navy) ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; color: white; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    
    /* סרגל בורסה רץ */
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #1c2e4a; color: #ffffff; padding: 10px 0; font-weight: bold; border-bottom: 1px solid #2e7bcf; }
    .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה רץ ---
st.markdown('<div class="ticker-wrap"><div class="ticker-move">📊 מדד ת"א ביטוח: +1.2% | הראל: ₪3,450 | הפניקס: ₪4,120 | מגדל: ₪620 | USD/ILS: 3.68 | ריבית ב"י: 4.5%</div></div>', unsafe_allow_html=True)

# --- 3. חיבור מתוקן ל-AI (מניעת שגיאת 404) ---
def init_ai():
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            # שימוש בשם המודל ללא קידומת models/ לתיקוף ב-v1beta
            return genai.GenerativeModel('gemini-1.5-flash')
    except Exception:
        return None
    return None

model = init_ai()

# --- 4. סרגל ניווט (Sidebar) ---
with st.sidebar:
    st.title("🏛️ ניהול פיקוח")
    company = st.selectbox("חברה מדווחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
    year = st.selectbox("שנה", ["2025", "2024"])
    quarter = st.radio("רבעון", ["Q1", "Q2", "Q3"])
    st.divider()
    
    # נתיב דינמי לקבצים
    fin_file = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    if model:
        st.success("מנוע AI מחובר ✅")
    else:
        st.error("AI לא מחובר - בדוק Secrets ❌")

# --- 5. גוף המערכת (Tabs) ---
st.title(f"ניתוח הוליסטי: {company}")

tab1, tab2, tab3, tab4 = st.tabs(["📊 IFRS 17 ורווחיות", "🛡️ יציבות וסולבנסי", "🧪 סימולטור רגישות", "ℹ️ הסבר"])

with tab1:
    st.subheader("ניתוח רווחיות ומגזרי פעילות (CSM)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("רווח כולל", "₪---M")
    c2.metric("יתרת CSM", "₪---B")
    c3.metric("ROE", "---%")
    c4.metric("פרמיות", "₪---M")

    if os.path.exists(fin_file):
        st.success(f"✅ דוח כספי זוהה בנתיב המערכת")
        if st.button("🚀 הפעל סריקת AI עמוקה"):
            if model:
                with st.spinner("ה-AI מנתח נתוני IFRS 17..."):
                    try:
                        with open(fin_file, "rb") as f:
                            pdf_data = f.read()
                        
                        # פרומפט מובנה עם דרישה לדיוק
                        response = model.generate_content([
                            "Analyze this insurance financial report. Extract: Net Profit, Total CSM balance, and ROE. Return results in Hebrew.",
                            {"mime_type": "application/pdf", "data": pdf_data}
                        ])
                        st.markdown("---")
                        st.markdown("### 🔍 ממצאי הניתוח:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"שגיאה בתקשורת עם המודל: {str(e)}")
            else:
                st.error("המערכת לא מצליחה להתחבר למפתח ה-API.")
    else:
        st.warning(f"קובץ חסר בנתיב: {fin_file}")

with tab2:
    st.subheader("מדדי Solvency II")
    st.metric("יחס סולבנסי משוער", "---%", "יעד: >100%")
    with st.popover("עזרה מקצועית"):
        st.write("יחס הסולבנסי מחושב כהון עצמי מוכר חלקי דרישת הון SCR.")

with tab3:
    st.subheader("סימולטור תרחישי קיצון")
    ir = st.slider("שינוי ריבית (בנקודות בסיס)", -100, 100, 0)
    st.info(f"השפעה חזויה על יחס סולבנסי: {ir * 0.1}%")

st.divider()
st.caption("Apex Pro - מערכת תומכת החלטות למפקח | 2026")
