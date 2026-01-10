import streamlit as st
import google.generativeai as genai
import os

# --- 1. הגדרות דף ועיצוב Dashboard ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-right: 5px solid #1c2e4a; }
    </style>
""", unsafe_allow_html=True)

# --- 2. חיבור למנוע ה-AI (Gemini) ---
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    return None

model = init_ai()

# --- 3. סרגל בורסה רץ (Ticker Tape) ---
st.markdown('<div style="background-color: #1c2e4a; color: white; padding: 10px; text-align: center; font-weight: bold;">📊 מדד ת"א ביטוח: +1.2% | הראל: ₪3,450 | תשואת אג"ח 10ש: 4.35% | USD/ILS: 3.68</div>', unsafe_allow_html=True)

# --- 4. סרגל ניווט (Sidebar) ---
with st.sidebar:
    st.title("🏛️ ניהול פיקוח")
    company = st.selectbox("חברה מדווחת", ["Harel"])
    year = st.selectbox("שנת דיווח", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    st.divider()
    
    # נתיב הקובץ שהעלית בגיטהאב
    fin_file = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    if model:
        st.success("מנוע AI מחובר ✅")
    else:
        st.error("חסר API Key ב-Secrets! ❌")

# --- 5. גוף המערכת - IFRS 17 וסולבנסי ---
st.title(f"ניתוח הוליסטי: {company} - {quarter}/{year}")

tab1, tab2, tab3 = st.tabs(["📊 IFRS 17 & רווחיות", "🛡️ יציבות (Solvency II)", "🧪 סימולטור"])

with tab1:
    st.subheader("ניתוח נתוני רווחיות ו-CSM")
    
    # יצירת מקום לנתונים (Placeholders)
    metrics_cols = st.columns(4)
    m1 = metrics_cols[0].empty()
    m2 = metrics_cols[1].empty()
    m3 = metrics_cols[2].empty()
    m4 = metrics_cols[3].empty()
    
    # ערכי ברירת מחדל
    m1.metric("רווח נקי", "₪---M")
    m2.metric("יתרת CSM", "₪---B")
    m3.metric("ROE", "---%")
    m4.metric("פרמיות ברוטו", "₪---M")

    if os.path.exists(fin_file):
        st.success(f"קובץ זוהה: financial_report.pdf")
        
        if st.button("🚀 הפעל ניתוח AI עמוק לנתוני IFRS 17"):
            if not model:
                st.error("אנא הגדר API Key ב-Secrets")
            else:
                with st.spinner("ה-AI סורק טבלאות ומחלץ נתונים..."):
                    try:
                        # קריאת הקובץ מה-GitHub
                        with open(fin_file, "rb") as f:
                            pdf_data = f.read()
                        
                        # ה-Prompt ההנדסי המדויק
                        prompt = f"""
                        Analyze the attached financial report for {company}. 
                        Extract the following 4 values for {quarter} {year}:
                        1. Net Profit (רווח נקי) in millions NIS.
                        2. Total CSM balance (יתרת CSM) in billions NIS.
                        3. Annualized ROE (תשואה להון).
                        4. Gross Earned Premiums (פרמיות שהורווחו ברוטו) in millions NIS.
                        Return only a list of values.
                        """
                        
                        # שליחה ל-AI
                        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_data}])
                        
                        # הצגת התוצאה הגולמית מתחת למדדים
                        st.markdown("### 🔍 פירוט ממצאי ה-AI:")
                        st.write(response.text)
                        
                        # כאן המפקח יכול לעדכן את המדדים ידנית או שנשדרג את הקוד לשליפה אוטומטית למשבצות
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"שגיאה בניתוח הקובץ: {str(e)}")
    else:
        st.warning(f"קובץ לא נמצא בנתיב: {fin_file}")

with tab2:
    st.info("כאן יוצגו נתוני יחס סולבנסי ברגע שתפעיל את סריקת דוח הסולבנסי.")
