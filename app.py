import streamlit as st
import time

# --- 1. הגדרות דף ועיצוב Deep Navy ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 15px; border-radius: 10px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem; }
    .ticker-wrap { background: #1c2e4a; color: white; padding: 10px; overflow: hidden; white-space: nowrap; border-bottom: 2px solid #2e7bcf; }
    .ticker { display: inline-block; animation: ticker 30s linear infinite; font-weight: bold; font-family: sans-serif; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .red-flag { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 5px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה רץ (Ticker Tape) ---
st.markdown('<div class="ticker-wrap"><div class="ticker">הראל השקעות +1.2% ▲ | הפניקס -0.4% ▼ | מגדל אחזקות +0.7% ▲ | כלל ביטוח +2.1% ▲ | מנורה מבטחים +0.3% ▲</div></div>', unsafe_allow_html=True)

# --- 3. סרגל צד (Sidebar) ---
with st.sidebar:
    st.title("🏛️ בקרת מפקח")
    company = st.selectbox("שם החברה", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
    year = st.selectbox("שנה", ["2025", "2024"])
    quarter = st.radio("רבעון", ["Q1", "Q2", "Q3"])
    st.divider()
    st.success("מחובר למאגר הנתונים: GitHub ✅")

# --- 4. לוח מחוונים ראשי (KPIs עם Popovers) ---
st.title(f"ניתוח הוליסטי: {company} - {year} {quarter}")

# דימוי נתונים לפי חברה (נתוני דמה להמחשה)
mock_data = {
    "רווח": "₪452M",
    "CSM": "₪12.4B",
    "ROE": "14.2%",
    "פרמיות": "₪8.1B",
    "נכסים": "₪340B"
}

cols = st.columns(5)
metrics = [
    {"label": "רווח כולל", "val": mock_data["רווח"], "info": "הרווח הכולל לפי IFRS 17. כולל רווח חתום ותשואות השקעה."},
    {"label": "יתרת CSM", "val": mock_data["CSM"], "info": "Contractual Service Margin - עתודת הרווח העתידית. מדד ליציבות ארוכת טווח."},
    {"label": "ROE", "val": mock_data["ROE"], "info": "תשואה להון - מודד את הרווחיות ביחס להון העצמי הממוצע."},
    {"label": "פרמיות ברוטו", "val": mock_data["פרמיות"], "info": "סך המכירות לפני ביטוח משנה. אינדיקטור לנתח שוק."},
    {"label": "סך נכסים", "val": mock_data["נכסים"], "info": "היקף המאזן הכולל (Total Assets) תחת ניהול הקבוצה."}
]

for i, m in enumerate(metrics):
    with cols[i]:
        st.metric(m['label'], m['val'], delta="+3%" if i != 1 else "-1.5%")
        st.popover("ℹ️ הסבר").write(m['info'])

# --- 5. טאבים לניתוח מעמיק ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 IFRS 17 & AI", "📈 יחסים פיננסיים", "🛡️ סולבנסי", "🕹️ סימולטור"])

with tab1:
    st.subheader("סריקה חכמה מבוססת AI (סימולציה)")
    if st.button("🚀 הרץ ניתוח דוח כספי"):
        with st.spinner("ה-AI סורק את ביאורי ה-CSM ומגזרי הפעילות..."):
            time.sleep(2)
            st.success("הסריקה הושלמה!")
            st.markdown(f"""
            ### 🔍 ממצאי ה-AI עבור {company}:
            * **ניתוח רווחיות:** נרשמה צמיחה ברווח החתום במגזר ביטוח חיים עקב עדכון הנחות דמוגרפיות.
            * **יתרת CSM:** חלה ירידה קלה ביתרה עקב שחרור רווח מואץ ברבעון הנוכחי.
            * **מגזרי פעילות:** מגזר הבריאות מציג יציבות עם יחס חתום (PAA) משופר.
            """)
            st.balloons()

with tab2:
    st.subheader("ניתוח יחסים פיננסיים (מאזן, רוו\"ה, תזרים)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("יחסי חתום")
        st.write("Combined Ratio: **92.4%**")
        st.write("Loss Ratio: **78.2%**")
        st.popover("ℹ️").write("יחס הפסדים (Loss Ratio) מודד את שיעור התביעות מתוך הפרמיות.")
    with c2:
        st.info("נזילות ותזרים")
        st.write("תזרים מפעילות: **₪1.2B**")
        st.write("יחס נזילות: **1.45**")
        st.popover("ℹ️").write("בוחן את היכולת לפרוע התחייבויות קצרות מועד.")
    with c3:
        st.info("🚩 דגלים אדומים")
        st.markdown('<p class="red-flag">🚩 עלייה חריגה בהוצאות הנהלה וכלליות (גידול של 12%)</p>', unsafe_allow_html=True)
        st.markdown('<p class="red-flag">🚩 תזרים מזומנים מהשקעות שלילי עקב רכישת נדל"ן מניב</p>', unsafe_allow_html=True)

with tab3:
    st.subheader("יציבות הון (Solvency II)")
    st.write("יחס כושר פירעון ליום 31.03.2025 (משוער):")
    st.progress(0.82, text="82% (מתחת ליעד הרגולטורי)")
    st.error("🚩 דגל אדום: יחס הסולבנסי ירד מתחת ל-100%. החברה נדרשת להציג תוכנית לחיזוק ההון.")

with tab4:
    st.subheader("סימולטור רגישות ותרחישי קיצון")
    rate = st.slider("שינוי בריבית (%)", -2.0, 2.0, 0.0, help="השפעה על שווי ההתחייבויות")
    market = st.slider("שינוי בשוק ההון (%)", -30, 0, 0, help="השפעה על תיק הנוסטרו")
    
    impact = (rate * 120) + (market * 45)
    st.metric("השפעה משוערת על יתרת ה-CSM", f"₪{impact}M", delta=impact)

st.divider()
st.caption("Apex Pro v1.0 | מערכת תומכת החלטות למפקח | 2026")
