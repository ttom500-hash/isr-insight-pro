import streamlit as st
import pandas as pd
import requests
import base64
import os
import plotly.express as px
import plotly.graph_objects as go

# --- 1. הגדרות עיצוב Deep Navy וסגנון רגולטורי ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 15px; border-radius: 10px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem; }
    .ticker-wrap { background: #1c2e4a; color: white; padding: 8px; overflow: hidden; white-space: nowrap; border-bottom: 2px solid #2e7bcf; }
    .ticker { display: inline-block; animation: ticker 40s linear infinite; font-weight: bold; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .red-flag { background-color: #441111; color: #ff4b4b; padding: 10px; border-radius: 5px; border-right: 5px solid #ff4b4b; margin-bottom: 10px; font-weight: bold; }
    .info-box { background-color: #16213e; padding: 15px; border-radius: 10px; border: 1px solid #2e7bcf; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה רץ (Ticker Tape) ---
st.markdown('<div class="ticker-wrap"><div class="ticker">הראל השקעות +1.2% ▲ | הפניקס -0.4% ▼ | מגדל אחזקות +0.7% ▲ | כלל ביטוח +2.1% ▲ | מנורה מבטחים +0.3% ▲ | מדד ת"א ביטוח +1.1% ▲</div></div>', unsafe_allow_html=True)

# --- 3. סרגל צד (Sidebar) - ניווט וחיפוש מתקדם ---
with st.sidebar:
    st.title("🏛️ בקרת מפקח")
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    st.header("🔍 פרמטרי חיפוש")
    company = st.selectbox("בחר חברה לניתוח", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
    year = st.selectbox("שנה", ["2025", "2024"])
    quarter = st.radio("רבעון", ["Q1", "Q2", "Q3"])
    
    st.divider()
    st.header("📊 השוואה בין חברות")
    compare_with = st.multiselect("בחר חברות להשוואה", ["Phoenix", "Migdal", "Clal", "Menora"], default=["Phoenix"])
    
    st.divider()
    st.caption(f"נתיב ב-GitHub: data/{company}/{year}/{quarter}/")

# --- 4. לוח מחוונים ראשי (5 KPIs עם הסברים) ---
st.title(f"דוח פיקוח הוליסטי: {company} ({year} {quarter})")

cols = st.columns(5)
kpi_data = [
    {"label": "רווח כולל", "val": "₪452M*", "info": "הרווח הכולל לאחר מס והתאמות IFRS 17. מייצג את הגידול האמיתי בהון המיוחס לבעלים."},
    {"label": "יתרת CSM", "val": "₪12.4B*", "info": "Contractual Service Margin: עתודת הרווח העתידית מחוזים קיימים. ירידה בנתון זה ללא צמיחה ב-New Business היא דגל אדום."},
    {"label": "ROE", "val": "14.2%*", "info": "תשואה להון: רווח כולל חלקי הון עצמי ממוצע. אינדיקטור ליעילות הניהולית וההונית."},
    {"label": "פרמיות ברוטו", "val": "₪8.1B*", "info": "סך הפרמיות שהורווחו ברוטו. משמש למדידת נתח שוק וצמיחה אורגנית."},
    {"label": "סך נכסים (AUM)", "val": "₪340B*", "info": "סך המאזן והנכסים המנוהלים. מעיד על עוצמת החברה והיקף האחריות הרגולטורית."}
]

for i, kpi in enumerate(kpi_data):
    with cols[i]:
        st.metric(kpi['label'], kpi['val'], delta="+2.1%")
        st.popover("ℹ️ הסבר לאנליסט").write(kpi['info'])

st.divider()

# --- 5. טאבים לניתוח מעמיק ---
tabs = st.tabs([
    "📂 IFRS 17 (פילוח)", 
    "💰 ניתוח השקעות", 
    "📈 יחסים ודגלים אדומים", 
    "🛡️ סולבנסי והון", 
    "⚖️ השוואה ענפית", 
    "🕹️ סימולטור"
])

# --- טאב 1: פילוח IFRS 17 (הבקשה לפילוח מגזרי) ---
with tabs[0]:
    st.subheader("פילוח מגזרי IFRS 17 (LoB)")
    col_lob1, col_lob2 = st.columns([2, 1])
    
    with col_lob1:
        # פילוח CSM לפי מגזרים
        lob_df = pd.DataFrame({
            "מגזר": ["ביטוח חיים", "בריאות", "ביטוח כללי"],
            "יתרת CSM": [8500, 2900, 1000],
            "CSM חדש": [450, 210, 85]
        })
        fig_lob = px.bar(lob_df, x="מגזר", y=["יתרת CSM", "CSM חדש"], title="פילוח CSM לפי מגזר (במיליוני ש"ח)", barmode="group")
        st.plotly_chart(fig_lob, use_container_width=True)
    
    with col_lob2:
        st.info("💡 תובנות מפירוק ה-CSM")
        st.write("- **ביטוח חיים:** המגזר הדומיננטי, שים לב לשחרור רווח (Release) מואץ.")
        st.write("- **בריאות:** צמיחה של 7% ב-CSM חדש (New Business).")
        st.write("- **כללי:** מודל PAA שולט, ה-CSM זניח יחסית.")
        st.popover("ℹ️ הסבר רגולטורי").write("IFRS 17 דורש הפרדה בין מודלים (GMM/PAA/VFA). כאן אנו מנתחים את תנועת ה-CSM.")

# --- טאב 2: ניתוח השקעות (הבקשה לפירוט השקעות) ---
with tabs[1]:
    st.subheader("פילוח תיק השקעות (נוסטרו ופוליסות משתתפות)")
    col_inv1, col_inv2 = st.columns(2)
    
    with col_inv1:
        inv_df = pd.DataFrame({
            "אפיק השקעה": ["אג\"ח ממשלתי", "אג\"ח קונצרני", "מניות", "נדל\"ן מניב", "מזומן/אחר"],
            "חשיפה %": [40, 25, 20, 10, 5]
        })
        fig_inv = px.pie(inv_df, values="חשיפה %", names="אפיק השקעה", title="התפלגות נכסים", hole=0.4)
        st.plotly_chart(fig_inv)
    
    with col_inv2:
        st.subheader("ניתוח תשואות וסיכונים")
        st.write("**תשואת נוסטרו ריאלית:** 3.8% (מעל הממוצע)")
        st.write("**חשיפה לנכסים לא סחירים:** 22% ℹ️")
        st.popover("ℹ️ הערת מפקח").write("חשיפה גבוהה לנכסים לא סחירים (נדל"ן, קרנות PE) דורשת בדיקת שערוכים ואיכות הערכות שווי.")
        st.markdown('<div class="red-flag">🚩 חריגה: חשיפה למניות במגזר הכללי עולה על המגבלה הפנימית.</div>', unsafe_allow_html=True)

# --- טאב 3: יחסים ודגלים אדומים (מאזן, רוו"ה, תזרים) ---
with tabs[2]:
    st.subheader("ניתוח דוחות כספיים קלאסי")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("📊 דוח רווח והפסד")
        st.write("**Loss Ratio (כללי):** 76.5% ℹ️")
        st.write("**Combined Ratio:** 94.2% ℹ️")
        st.popover("ℹ️").write("Combined Ratio מעל 100% מעיד על הפסד חתומי.")
    with c2:
        st.info("💧 תזרים ונזילות")
        st.write("**תזרים מפעילות:** ₪1.1B ℹ️")
        st.write("**יחס כיסוי נזילות:** 1.3 ℹ️")
    with c3:
        st.info("⚖️ יחסי מאזן")
        st.write("**מינוף (חוב/הון):** 1.4 ℹ️")
        st.write("**הון לנכסים:** 5.5% ℹ️")

    st.subheader("🚩 דגלים אדומים למפקח")
    st.markdown('<div class="red-flag">🚩 דגל אדום: עלייה חריגה בהפרשות לתביעות מעבר לצפי האקטוארי.</div>', unsafe_allow_html=True)
    st.markdown('<div class="red-flag">🚩 דגל אדום: יחס נזילות נמוך מ-1.1 במגזר ביטוח חיים.</div>', unsafe_allow_html=True)

# --- טאב 4: סולבנסי והון ---
with tabs[3]:
    st.subheader("יציבות הון (Solvency II)")
    col_sol1, col_sol2 = st.columns(2)
    with col_sol1:
        st.metric("יחס כושר פירעון (Est.)", "104%", delta="-2%")
        st.progress(0.88, text="יחס סולבנסי מול יעד רגולטורי")
    with col_sol2:
        st.write("**הון רובד 1 (Tier 1):** ₪8.2B")
        st.write("**הון רובד 2 (Tier 2):** ₪1.3B")
        st.popover("ℹ️ איכות ההון").write("הון רובד 1 הוא האיכותי ביותר. רובד 2 מורכב לרוב מחוב נחות.")

# --- טאב 5: השוואה ענפית (הבקשה להשוואה בין חברות) ---
with tabs[4]:
    st.subheader(f"השוואת {company} מול {', '.join(compare_with)}")
    bench_data = pd.DataFrame({
        "חברה": [company] + compare_with,
        "יחס סולבנסי": [104, 112, 98, 108][:len(compare_with)+1],
        "ROE %": [14.2, 12.5, 15.1, 11.8][:len(compare_with)+1]
    })
    fig_bench = px.bar(bench_data, x="חברה", y="יחס סולבנסי", color="חברה", title="השוואת חוסן הוני (יחס סולבנסי %)")
    st.plotly_chart(fig_bench)
    st.table(bench_data)

# --- טאב 6: סימולטור רגישות ---
with tabs[5]:
    st.subheader("סימולטור תרחישי קיצון")
    s_rate = st.slider("שינוי בריבית (%)", -2.0, 2.0, 0.0)
    s_market = st.slider("שינוי במניות (%)", -30, 0, 0)
    impact = (s_rate * 140) + (s_market * 55)
    st.metric("השפעה חזויה על ה-CSM", f"₪{impact}M", delta=impact)

st.divider()
st.caption("Apex Pro v1.0 | פלטפורמת פיקוח רגולטורית מבוססת AI | 2026")
