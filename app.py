import streamlit as st
import google.generativeai as genai
import os
import pandas as pd

# --- 1. הגדרות דף ועיצוב יוקרתי (Deep Navy Style) ---
st.set_page_config(page_title="מערכת פיקוח הוליסטית", layout="wide")

st.markdown("""
    <style>
    /* עיצוב כללי */
    .main { background-color: #f4f7f9; }
    
    /* סרגל בורסה רץ (Ticker Tape) */
    @keyframes ticker {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    .ticker-wrap {
        width: 100%; overflow: hidden; background-color: #1c2e4a; 
        color: #ffffff; padding: 10px 0; font-family: 'Arial'; font-weight: bold;
    }
    .ticker-move {
        display: inline-block; white-space: nowrap; 
        animation: ticker 30s linear infinite;
    }
    
    /* כרטיסי אינדיקטורים */
    .stMetric {
        background-color: #ffffff; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-right: 5px solid #1c2e4a;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה רץ (Ticker Tape) ---
st.markdown("""
    <div class="ticker-wrap">
        <div class="ticker-move">
            📊 מדד ת"א ביטוח: +1.2% | הראל: ₪3,450 (+0.5%) | הפניקס: ₪4,120 (+0.8%) | תשואת אג"ח 10ש: 4.35% | USD/ILS: 3.68 | ריבית בנק ישראל: 4.5%
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 3. חיבור למנוע ה-AI (Gemini 1.5 Pro) ---
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    return None

model = init_ai()

# --- 4. סרגל ניווט (Sidebar) לפי האפיון ---
with st.sidebar:
    st.title("🏛️ ניהול פיקוח")
    company = st.selectbox("חברה מדווחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
    year = st.selectbox("שנת דיווח", ["2025", "2024"])
    quarter = st.radio("רבעון", ["Q1", "Q2", "Q3"])
    
    st.divider()
    # דינמיקה של נתיבי קבצים
    base_path = f"data/{company}/{year}/{quarter}"
    fin_file = f"{base_path}/financial/financial_report.pdf"
    sol_file = f"{base_path}/solvency/solvency_report.pdf"
    
    if model:
        st.success("מנוע AI מחובר (Gemini 1.5 Pro) ✅")
    else:
        st.warning("ממתין לחיבור API Key ב-Secrets ❌")

# --- 5. גוף המערכת - חלוקה לפי פיצ'רים (Tabs) ---
st.title(f"ניתוח הוליסטי: {company}")
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 ביצועים ורווחיות (IFRS 17)", 
    "🛡️ יציבות וסולבנסי", 
    "🧪 סימולטור רגישות", 
    "ℹ️ חלון הסבר מקצועי"
])

# --- טאב 1: רווחיות (IFRS 17) ---
with tab1:
    st.subheader("ניתוח רווחיות לפי IFRS 17")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("רווח כולל", "₪---M", "ממתין")
    c2.metric("יתרת CSM", "₪---B", "ממתין")
    c3.metric("ROE (משוער)", "---%", "ממתין")
    c4.metric("פרמיות ברוטו", "₪---M", "ממתין")

    if os.path.exists(fin_file):
        if st.button("🚀 הפעל סריקת AI לניתוח CSM ומגזרים"):
            with st.spinner("ה-AI מנתח טבלאות IFRS 17..."):
                # כאן תבוצע השליפה האמיתית
                st.info("בשלב זה המערכת מוכנה לשלוף את נתוני ה-CSM מהקובץ.")
    else:
        st.error(f"קובץ פיננסי לא נמצא בנתיב: {fin_path}")

# --- טאב 2: יציבות (Solvency II) ---
with tab2:
    st.subheader("כושר פירעון ויציבות הונית")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("יחס סולבנסי (SCR Ratio)", "---%", "יעד: >100%")
    col_b.metric("הון עצמי מוכר", "₪---B")
    col_c.metric("דרישת הון (SCR)", "₪---M")
    
    with st.popover("🔍 מהו יחס סולבנסי?"):
        st.write("יחס כושר הפירעון (Solvency II) מודד את היחס בין ההון המוכר של החברה לבין דרישת ההון המינימלית שהרגולטור מחייב (SCR).")

# --- טאב 3: סימולטור רגישות (קיצון) ---
with tab3:
    st.subheader("סימולטור תרחישי קיצון אינטראקטיבי")
    interest_rate = st.slider("שינוי בעקומת הריבית (bps)", -100, 100, 0)
    equity_drop = st.slider("ירידה בשוק המניות (%)", 0, 40, 0)
    
    st.info(f"השפעה משוערת על יחס הסולבנסי: {interest_rate * 0.2 - equity_drop * 1.5}%")

# --- טאב 4: הסבר מקצועי ---
with tab4:
    st.subheader("מדריך למפקח")
    st.write("""
    המערכת מנתחת את דוחות חברות הביטוח בהתאם לסטנדרטים הבינלאומיים:
    - **IFRS 17:** ניתוח חוזי ביטוח לפי מודל ה-CSM.
    - **Solvency II:** ניתוח יציבות הונית מבוססת סיכון.
    """)

st.divider()
st.caption("מערכת תומכת החלטות - פותח עבור ניתוח חברות ביטוח 2026")
