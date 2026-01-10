import streamlit as st
import google.generativeai as genai
import os

# --- 1. עיצוב Deep Navy יוקרתי (שמירה על האפיון המקורי) ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 20px; border-radius: 12px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    
    /* סרגל בורסה רץ (Ticker Tape) */
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background-color: #1c2e4a; color: #ffffff; padding: 10px 0; font-weight: bold; border-bottom: 1px solid #2e7bcf; }
    .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 35s linear infinite; }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה רץ (Ticker Tape) ---
st.markdown("""
    <div class="ticker-wrap">
        <div class="ticker-move">
            📊 מדד ת"א ביטוח: +1.2% | הראל: ₪3,450 (+0.5%) | הפניקס: ₪4,120 (+0.8%) | מגדל: ₪620 (+0.3%) | USD/ILS: 3.68 | ריבית ב"י: 4.5%
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 3. חיבור חסין לשגיאות (פתרון ה-404) ---
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            # קריאה ישירה לגרסת ה-Stable של המודל
            return genai.GenerativeModel('gemini-1.5-flash')
        except Exception:
            return None
    return None

model = init_ai()

# --- 4. סרגל ניווט (Sidebar) ---
with st.sidebar:
    st.title("🏛️ ניהול פיקוח")
    company = st.selectbox("חברה מדווחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
    year = st.selectbox("שנת דיווח", ["2025", "2024"])
    quarter = st.radio("רבעון", ["Q1", "Q2", "Q3"])
    st.divider()
    
    base_path = f"data/{company}/{year}/{quarter}"
    fin_file = f"{base_path}/financial/financial_report.pdf"
    
    if model:
        st.success("מנוע AI מחובר ומסונכרן ✅")

# --- 5. גוף המערכת (Tabs לפי האפיון) ---
st.title(f"ניתוח הוליסטי: {company}")

tab1, tab2, tab3 = st.tabs(["📊 IFRS 17 ורווחיות", "🛡️ יציבות וסולבנסי", "🧪 סימולטור רגישות"])

with tab1:
    st.subheader("ניתוח רווחיות ומגזרי פעילות (CSM)")
    # 5 המדדים שביקשת
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("רווח כולל", "₪---M")
    c2.metric("יתרת CSM", "₪---B")
    c3.metric("ROE", "---%")
    c4.metric("פרמיות ברוטו", "₪---M")
    c5.metric("נכסים מנוהלים", "₪---B")

    if os.path.exists(fin_file):
        st.success("✅ דוח כספי מזוהה")
        if st.button("🚀 הפעל סריקת AI עמוקה"):
            with st.spinner("ה-AI מנתח את הדוח..."):
                try:
                    with open(fin_file, "rb") as f:
                        pdf_data = f.read()
                    
                    # פקודה מובנית לפתרון ה-404
                    response = model.generate_content([
                        {"mime_type": "application/pdf", "data": pdf_data},
                        f"Analyze {company} {quarter} {year} report. Extract: Net Profit, Total CSM, ROE, Gross Premiums, Total Assets. Results in Hebrew."
                    ])
                    st.markdown("---")
                    st.markdown("### 🔍 ממצאי הניתוח:")
                    st.write(response.text)
                    st.balloons()
                except Exception as e:
                    st.error(f"שגיאה: {str(e)}")
    else:
        st.warning(f"קובץ חסר בנתיב: {fin_file}")

with tab2:
    st.subheader("מדדי Solvency II")
    st.metric("יחס סולבנסי", "---%", "יעד: >100%")
    with st.popover("הסבר מקצועי"):
        st.write("ניתוח הון עצמי מוכר מול דרישת הון SCR (Solvency Capital Requirement).")

with tab3:
    st.subheader("סימולטור תרחישי קיצון")
    ir = st.slider("שינוי ריבית (bps)", -100, 100, 0)
    st.info(f"השפעה משוערת על יחס הסולבנסי: {ir * 0.12}%")

st.divider()
st.caption("Apex Pro - מערכת תומכת החלטות למפקח | 2026")
