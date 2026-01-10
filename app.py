import streamlit as st
import pandas as pd
import requests
import base64
import os
import plotly.express as px

# --- 1. הגדרות עיצוב וסטייל (Deep Navy) ---
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
    </style>
""", unsafe_allow_html=True)

# --- 2. סרגל בורסה רץ ---
st.markdown('<div class="ticker-wrap"><div class="ticker">הראל השקעות +1.2% ▲ | הפניקס -0.4% ▼ | מגדל אחזקות +0.7% ▲ | כלל ביטוח +2.1% ▲ | מנורה מבטחים +0.3% ▲</div></div>', unsafe_allow_html=True)

# --- 3. סרגל צד (ניווט, חיפוש והשוואה) ---
with st.sidebar:
    st.title("🏛️ בקרת מפקח")
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    st.header("🔍 חיפוש וסינון")
    company = st.selectbox("בחר חברה", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
    year = st.selectbox("שנה", ["2025", "2024"])
    quarter = st.radio("רבעון", ["Q1", "Q2", "Q3"])
    
    st.divider()
    st.header("📊 השוואה ענפית")
    compare_with = st.multiselect("השוואה מול חברות אחרות", ["Phoenix", "Migdal", "Clal", "Menora"], default=["Phoenix"])

# --- 4. לוח מחוונים ראשי (5 KPIs) ---
st.title(f"דוח פיקוח הוליסטי: {company} - {year} {quarter}")

cols = st.columns(5)
kpis = [
    {"label": "רווח כולל", "val": "₪452M", "info": "הרווח הכולל המיוחס לבעלים לפי תקן IFRS 17."},
    {"label": "יתרת CSM", "val": "₪12.4B", "info": "עתודת הרווח העתידית בגין חוזים קיימים (מנוע הרווח)."},
    {"label": "ROE", "val": "14.2%", "info": "תשואה להון - יעילות הקצאת ההון של הקבוצה."},
    {"label": "פרמיות ברוטו", "val": "₪8.1B", "info": "היקף הפעילות החתומית (Top Line)."},
    {"label": "סך נכסים (AUM)", "val": "₪340B", "info": "סך המאזן והנכסים המנוהלים על ידי החברה."}
]

for i, kpi in enumerate(kpis):
    with cols[i]:
        st.metric(kpi['label'], kpi['val'])
        st.popover("ℹ️ הסבר").write(kpi['info'])

st.divider()

# --- 5. טאבים לניתוח מעמיק ---
t1, t2, t3, t4, t5, t6 = st.tabs(["📂 IFRS 17", "💰 השקעות", "📈 יחסים", "🛡️ סולבנסי", "⚖️ השוואה", "🕹️ סימולטור"])

# --- טאב 1: פילוח IFRS 17 ---
with t1:
    st.subheader("פילוח מגזרי וביצועי IFRS 17")
    lob_df = pd.DataFrame({
        "מגזר": ["חיים", "בריאות", "כללי"],
        "CSM קיים": [8200, 2500, 950],
        "CSM חדש": [350, 180, 45]
    })
    # התיקון כאן: שימוש בגרש בודד ב-title כדי לאפשר מרכאות בש"ח
    fig_lob = px.bar(lob_df, x="מגזר", y=["CSM קיים", "CSM חדש"], title='פילוח CSM לפי מגזר (במיליוני ש"ח)', barmode="group", color_discrete_sequence=['#2e7bcf', '#1c2e4a'])
    st.plotly_chart(fig_lob, use_container_width=True)

# --- טאב 2: פילוח השקעות ---
with t2:
    st.subheader("ניתוח תיק השקעות (נוסטרו)")
    inv_df = pd.DataFrame({"אפיק": ["אג\"ח", "מניות", "נדל\"ן", "הלוואות", "מזומן"], "חשיפה %": [45, 20, 15, 12, 8]})
    fig_inv = px.pie(inv_df, values="חשיפה %", names="אפיק", hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_inv)
    st.info("חשיפה לנכסים לא סחירים: 24% | תשואת תיק נוסטרו: 4.1%")

# --- טאב 3: יחסים ודגלים אדומים ---
with t3:
    st.subheader("מדדי רווחיות ותזרים")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Loss Ratio:** 76.4% | **Combined Ratio:** 93.1%")
        st.write("**יחס הוצאות הנהלה:** 14.8%")
    with c2:
        st.write("**תזרים מפעילות:** ₪1.15B | **יחס כיסוי נזילות:** 1.35")
    
    st.subheader("🚩 דגלים אדומים למפקח")
    st.markdown('<div class="red-flag">🚩 דגל אדום: עלייה חריגה בשיעור ביטול פוליסות (Lapse Rate) במגזר החיים.</div>', unsafe_allow_html=True)
    st.markdown('<div class="red-flag">🚩 דגל אדום: יחס תזרים מזומנים שלילי מפעילות השקעה (מעקב נדרש).</div>', unsafe_allow_html=True)

# --- טאב 4: סולבנסי ---
with t4:
    st.subheader("יציבות הון (Solvency II)")
    st.metric("יחס כושר פירעון (Est.)", "106%", delta="+2%")
    st.progress(0.88, text="יציבות הונית מול יעד רגולטורי")

# --- טאב 5: השוואה ענפית ---
with t5:
    st.subheader("השוואת ביצועים מול חברות נבחרות")
    comp_df = pd.DataFrame({
        "חברה": [company] + compare_with,
        "ROE %": [14.2, 12.8, 11.5, 13.1][:len(compare_with)+1],
        "Solvency %": [106, 110, 98, 104][:len(compare_with)+1]
    })
    st.bar_chart(comp_df.set_index("חברה")["Solvency %"])
    st.table(comp_df)

# --- טאב 6: סימולטור רגישות ---
with t6:
    st.subheader("סימולטור תרחישי קיצון")
    rate = st.slider("שינוי בריבית (%)", -2.0, 2.0, 0.0)
    market = st.slider("שינוי בשוק ההון (%)", -30, 0, 0)
    st.metric("השפעה חזויה על ה-CSM", f"₪{rate * 140 + market * 50}M")

st.divider()
st.caption("Apex Pro v1.0 | Integrated Supervisory System | 2026")
