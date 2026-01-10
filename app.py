import streamlit as st
import pandas as pd
import requests
import base64
import os
import plotly.express as px
import plotly.graph_objects as go

# --- 1. הגדרות עיצוב וסטייל (Deep Navy) ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1c2e4a; padding: 15px; border-radius: 10px; border-right: 5px solid #2e7bcf; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem; }
    .ticker-wrap { background: #1c2e4a; color: white; padding: 8px; overflow: hidden; white-space: nowrap; border-bottom: 2px solid #2e7bcf; }
    .ticker { display: inline-block; animation: ticker 50s linear infinite; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .red-flag { background-color: #441111; color: #ff4b4b; padding: 10px; border-radius: 5px; border-right: 5px solid #ff4b4b; margin-bottom: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה רץ (ישראל ועולם) ---
ticker_text = (
    "🇮🇱 ת\"א-35: 2,045.2 (+0.8%) | ת\"א-ביטוח: 2,540.1 (+1.4%) | ת\"א-125: 2,110.5 (+0.6%) | "
    "🇺🇸 S&P 500: 5,120.3 (+0.4%) | NASDAQ: 16,250.8 (+0.7%) | DOW JONES: 39,120.1 (-0.1%) | "
    "🇪🇺 DAX: 18,150.4 (+0.2%) | 🇯🇵 NIKKEI: 38,500.5 (-0.3%) | הראל: +1.2% | הפניקס: -0.5% | מגדל: +0.8%"
)
st.markdown(f'<div class="ticker-wrap"><div class="ticker">{ticker_text}</div></div>', unsafe_allow_html=True)

# --- 3. סרגל צד (ניווט וסינון) ---
with st.sidebar:
    st.title("🏛️ חדר בקרה - Apex Pro")
    st.header("🔍 חיפוש ופילוח")
    company = st.selectbox("בחר חברה לניתוח", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
    year = st.selectbox("שנה", ["2025", "2024"])
    quarter = st.radio("רבעון", ["Q1", "Q2", "Q3"])
    
    st.divider()
    st.header("📊 השוואה ענפית")
    compare_list = st.multiselect("חברות להשוואה", ["Phoenix", "Migdal", "Clal", "Menora"], default=["Phoenix"])
    
    st.divider()
    st.caption(f"נתיב קבצים: data/{company}/{year}/{quarter}/")

# --- 4. לוח מחוונים ראשי (5 KPIs עם הסברים) ---
st.title(f"ניתוח פיקוח הוליסטי: {company} ({year} {quarter})")

cols = st.columns(5)
kpis = [
    {"label": "רווח כולל", "val": "₪452M", "info": "הרווח הכולל המיוחס לבעלי המניות תחת IFRS 17. כולל רווח חתום ותשואות השקעה."},
    {"label": "יתרת CSM", "val": "₪12.4B", "info": "Contractual Service Margin: עתודת הרווח העתידית בגין חוזים קיימים."},
    {"label": "ROE", "val": "14.2%", "info": "תשואה להון: רווח כולל חלקי הון עצמי ממוצע. מודד את יעילות הקצאת ההון."},
    {"label": "פרמיות ברוטו", "val": "₪8.1B", "info": "סך הפרמיות שהורווחו ברוטו (Top Line). אינדיקטור לצמיחה ונתח שוק."},
    {"label": "סך נכסים (AUM)", "val": "₪340B", "info": "היקף המאזן והנכסים המנוהלים. מעיד על עוצמת החברה והיקף האחריות."}
]

for i, kpi in enumerate(kpis):
    with cols[i]:
        st.metric(kpi['label'], kpi['val'], delta="+2.5%")
        st.popover("ℹ️ הסבר").write(kpi['info'])

st.divider()

# --- 5. טאבים לניתוח מעמיק (כל הפיצ'רים המקצועיים) ---
tabs = st.tabs([
    "📂 IFRS 17 (פילוח)", 
    "💰 ניתוח השקעות", 
    "📈 יחסים פיננסיים", 
    "🛡️ סולבנסי ואיכות הון", 
    "⚖️ השוואה ענפית", 
    "🕹️ סימולטור קיצון"
])

# --- טאב 1: IFRS 17 כולל חוזים מפסידים ---
with tabs[0]:
    st.subheader("פילוח מגזרי ותנועת CSM")
    c1, c2 = st.columns([2, 1])
    with c1:
        ifrs_df = pd.DataFrame({
            "מגזר": ["חיים", "בריאות", "כללי"],
            "CSM קיים": [8200, 2500, 950],
            "חוזים מפסידים (Onerous)": [120, 45, 15]
        })
        # שימוש בגרש בודד ב-title למניעת שגיאת Syntax בש"ח
        fig_ifrs = px.bar(ifrs_df, x="מגזר", y=["CSM קיים", "חוזים מפסידים (Onerous)"], 
                          title='פילוח CSM מול חוזים מפסידים (במיליוני ש"ח)', barmode="group",
                          color_discrete_sequence=['#2e7bcf', '#ff4b4b'])
        st.plotly_chart(fig_ifrs, use_container_width=True)
    with c2:
        st.info("💡 דגשים רגולטוריים")
        st.write(f"**סך חוזים מפסידים:** ₪180M")
        st.popover("ℹ️ משמעות").write("חוזים מפסידים מוכרים מידית ברווח והפסד. גידול כאן מעיד על תמחור חסר במוצרים חדשים.")

# --- טאב 2: ניתוח השקעות (פירוט נכסים ותשואות) ---
with tabs[1]:
    st.subheader("פילוח תיק השקעות נוסטרו")
    inv_df = pd.DataFrame({"אפיק": ["אג\"ח ממשלתי", "אג\"ח קונצרני", "מניות", "נדל\"ן", "אחר"], "חשיפה %": [40, 25, 20, 10, 5]})
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        st.plotly_chart(px.pie(inv_df, values="חשיפה %", names="אפיק", hole=0.5, title="התפלגות נכסים"))
    with col_inv2:
        st.write("**תשואת נוסטרו ריאלית:** 3.8%")
        st.write("**חשיפה לנכסים לא סחירים:** 22% ℹ️")
        st.popover("ℹ️ ניהול סיכונים").write("חשיפה גבוהה לנכסים לא סחירים (PE, נדל\"ן ריאלי) דורשת מעקב אחר איכות השערוכים.")

# --- טאב 3: יחסים פיננסיים מורחבים ודגלים אדומים ---
with tabs[2]:
    st.subheader("ניתוח יחסים (מאזן, רוו\"ה ותזרים)")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.info("📊 רווחיות וחתום")
        st.write("**Loss Ratio:** 76.5% | **Combined:** 93.2%")
        st.write("**Expense Ratio:** 14.2% | **ROA:** 1.1%")
    with r2:
        st.info("💧 נזילות ותזרים")
        st.write("**יחס כיסוי נזילות (LCR):** 1.45")
        st.write("**תזרים מפעילות:** ₪1.1B")
    with r3:
        st.info("⚖️ מבנה הון")
        st.write("**יחס הון לנכסים:** 5.4%")
        st.write("**מינוף פיננסי:** 1.35")
    
    st.subheader("🚩 דגלים אדומים למפקח")
    st.markdown('<div class="red-flag">🚩 דגל אדום: עלייה חריגה ב-Loss Ratio במגזר הבריאות לעומת ממוצע רב-שנתי.</div>', unsafe_allow_html=True)
    st.markdown('<div class="red-flag">🚩 דגל אדום: יחס נזילות נמוך מ-1.1 במגזר ביטוח חיים - נדרש מעקב תזרים.</div>', unsafe_allow_html=True)

# --- טאב 4: סולבנסי ואיכות הון (Tier 1/2) ---
with tabs[3]:
    st.subheader("ניתוח חוסן הוני ואיכות ההון")
    s1, s2 = st.columns(2)
    with s1:
        st.metric("יחס כושר פירעון (Est.)", "104%", delta="-2%")
        st.write("**הון מוכר כולל:** ₪9.8B")
        st.progress(0.88, text="יציבות הון מול יעד רגולטורי (100%)")
    with s2:
        cap_df = pd.DataFrame({"סוג הון": ["רובד 1 (Tier 1)", "רובד 2 (Tier 2)"], "סכום": [8500, 1300]})
        st.plotly_chart(px.bar(cap_df, x="סוג הון", y="סכום", color="סוג הון", title='הרכב הון (במיליוני ש"ח)', color_discrete_sequence=['#2e7bcf', '#16213e']))

# --- טאב 5: השוואה ענפית מורחבת (Benchmarking) ---
with tabs[4]:
    st.subheader("השוואת ביצועים מול קבוצת ייחוס")
    bench_df = pd.DataFrame({
        "חברה": [company] + compare_list,
        "Solvency %": [104, 112, 108, 98, 105][:len(compare_list)+1],
        "ROE %": [14.2, 12.5, 11.8, 15.0, 13.5][:len(compare_list)+1],
        "CSM (B)": [12.4, 15.1, 10.2, 9.8, 11.5][:len(compare_list)+1]
    })
    st.dataframe(bench_df.set_index("חברה"), use_container_width=True)
    # תרשים בועות להשוואה רב-ממדית
    fig_bench = px.scatter(bench_df, x="Solvency %", y="ROE %", text="חברה", size="CSM (B)", color="חברה",
                           title="מיצוי הון מול רווחיות (גודל בועה = יתרת CSM)")
    st.plotly_chart(fig_bench, use_container_width=True)

# --- טאב 6: סימולטור תרחישי קיצון מורחב (ריבית, מניות, ביטולים, רעידת אדמה) ---
with tabs[5]:
    st.subheader("סימולטור תרחישי קיצון (Stress Test)")
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        st.write("**תרחישי שוק:**")
        s_rate = st.slider("שינוי ריבית (%)", -2.0, 2.0, 0.0)
        s_market = st.slider("נפילה בשוק המניות (%)", -30, 0, 0)
    with col_sim2:
        st.write("**תרחישי ביטוח וקטסטרופה:**")
        s_lapse = st.slider("גידול בשיעור ביטולים (Lapse) %", 0, 50, 0)
        s_quake = st.checkbox("תרחיש רעידת אדמה (Earthquake Scenario)")
    
    # לוגיקת השפעה משולבת
    impact = (s_rate * 140) + (s_market * 55) + (s_lapse * -35)
    if s_quake: impact -= 850
    st.metric("השפעה חזויה על יתרת ה-CSM/הון", f"₪{impact}M", delta=impact)
    st.popover("ℹ️ מתודולוגיה").write("החישוב מבוסס על מקדמי הרגישות בביאור ניהול סיכונים ובניתוח תרחישי קיצון של החברה.")

st.divider()
st.caption("Apex Pro v1.0 | פלטפורמת פיקוח רגולטורית הוליסטית | 2026")
