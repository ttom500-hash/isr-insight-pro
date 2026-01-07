import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import date

# --- הגדרות Apex Branding ---
st.set_page_config(page_title="Apex - SupTech Intelligence", page_icon="⛰️", layout="wide")

# --- פונקציית טיימר לדיווחים ---
def get_countdown():
    today = date.today()
    # מועד הדיווח השנתי הבא (דוחות 2025 מתפרסמים עד סוף מרץ 2026)
    deadline = date(2026, 3, 31)
    delta = deadline - today
    return delta.days

@st.cache_data
def load_data():
    path = 'data/database.csv'
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

def metric_with_help(label, value, title, description, formula=None, is_main=False):
    """הצגת מדד עם חלון הסבר (Popover)"""
    if is_main:
        st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(title)
        st.write(description)
        if formula:
            st.write("**נוסחה:**")
            st.latex(formula)

df = load_data()

if not df.empty:
    # --- Sidebar: Apex Logo, Timer & Filters ---
    with st.sidebar:
        st.title("⛰️ Apex")
        st.caption("SupTech Intelligence & Foresight")
        st.divider()
        
        # טיימר דיווחים
        days_left = get_countdown()
        st.subheader("⏳ ספירה לאחור לדיווח")
        st.metric("ימים לפרסום שנתי", f"{days_left}", delta="-31/03", delta_color="inverse")
        st.progress(max(0, min(100, (365-days_left)/365)))
        
        st.divider()
        
        # סינון היררכי (נשמר בדיוק כפי שהיה)
        st.header("🔍 חיפוש וסינון")
        sel_comp = st.selectbox("1. בחר חברה:", sorted(df['company'].unique()))
        sel_year = st.selectbox("2. בחר שנה:", sorted(df[df['company']==sel_comp]['year'].unique(), reverse=True))
        sel_q = st.selectbox("3. בחר רבעון:", sorted(df[(df['company']==sel_comp) & (df['year']==sel_year)]['quarter'].unique(), reverse=True))
        
        d = df[(df['company']==sel_comp) & (df['year']==sel_year) & (df['quarter']==sel_q)].iloc[0]

    # --- גוף האפליקציה ---
    st.title(f"ניתוח פיננסי: {sel_comp}")
    st.caption(f"תקופה: {sel_q} {sel_year} | מערכת Apex | אימות: {d['data_source']}")

    # --- שורת KPIs עליונה (5 מדדים כפי שביקשת) ---
    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        metric_with_help("יחס כושר פירעון", f"{d['solvency_ratio']}%", "יחס כושר פירעון (Solvency II)", "המדד העליון ליציבות הונית.", r"Ratio = \frac{Own \ Funds}{SCR}", is_main=True)
    with m2:
        metric_with_help("מרווח שירות (CSM)", f"₪{d['csm_total']}B", "Contractual Service Margin", "הרווח העתידי מהתחייבויות ביטוחיות.", formula=None, is_main=True)
    with m3:
        total_aum = d['vfa_assets_aum'] + d['inv_contracts_aum'] + d['pension_aum'] + d['provident_aum']
        st.metric("סך נכסים (AUM)", f"₪{round(total_aum, 1)}B")
    with m4:
        st.metric("תשואה להון (ROE)", f"{d['roe']}%")
    with m5:
        st.metric("הון רובד 1", f"{d['tier1_ratio']}%")

    # --- דגלים אדומים ---
    flags = []
    if d['solvency_ratio'] < 150: flags.append(f"🚩 סולבנסי ({d['solvency_ratio']}%) נמוך מהיעד.")
    if d['combined_ratio'] > 100: flags.append(f"🚩 הפסד חיתומי ({d['combined_ratio']}%).")
    if flags:
        with st.expander("🚨 התראות Apex (Red Flags)", expanded=True):
            for f in flags: st.warning(f)

    st.divider()

    # --- טאבים (IFRS 17, יחסים, נכסים, Stress Test) ---
    tabs = st.tabs(["📑 IFRS 17 ומגזרים", "📈 מרכז יחסים פיננסיים", "💰 נכסים מנוהלים", "⛈️ Stress Test"])

    with tabs[0]:
        st.subheader("ניתוח מגזרי ומודלי מדידה (GMM/VFA/PAA)")
        c1, c2 = st.columns(2)
        with c1:
            s_df = pd.DataFrame({'Sector': ['חיים', 'בריאות', 'כללי'], 'Val': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.pie(s_df, names='Sector', values='Val', title="פילוח CSM מגזרי", hole=0.4), use_container_width=True)
        with c2:
            m_df = pd.DataFrame({'Model': ['VFA (משתתפות)', 'PAA (מפושט)', 'GMM (רגיל)'], 'Share': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(m_df, names='Model', values='Share', title="תמהיל מודלים חשבונאיים", hole=0.5), use_container_width=True)

    with tabs[1]:
        st.subheader("📊 יחסים פיננסיים - לחץ על ℹ️ להסבר")
        r1, r2, r3 = st.columns(3)
        with r1:
            metric_with_help("שיעור שחרור CSM", f"{d['csm_release_rate']}%", "Release Rate", "קצב הפיכת רווח עתידי לרווח בפועל.", r"Rate = \frac{Recognized \ CSM}{Opening \ CSM}", is_main=True)
        with r2:
            metric_with_help("מרווח עסקים חדשים", f"{d['new_biz_margin']}%", "NB Margin", "רווחיות המכירות החדשות.", r"Margin = \frac{New \ Biz \ CSM}{PVFP}", is_main=True)
        with r3:
            metric_with_help("יחס משולב (PAA)", f"{d['combined_ratio']}%", "Combined Ratio", "רווחיות חיתומית (מעל 100% = הפסד).", is_main=True)

    with tabs[2]:
        st.subheader("פילוח נכסים מנוהלים (AUM) וחשיפת נוסטרו")
        ca, cb = st.columns([2, 1])
        with ca:
            a_df = pd.DataFrame({'סוג': ['פנסיה', 'גמל', 'השקעות', 'VFA'], 'מיליארד': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]})
            st.plotly_chart(px.bar(a_df, x='סוג', y='מיליארד', color='סוג'), use_container_width=True)
        with cb:
            n_df = pd.DataFrame({'Asset': ['נדל"ן', 'מניות', 'אלטרנטיבי'], 'Pct': [d['re_pct'], d['equity_pct'], d['alts_pct']]})
            st.plotly_chart(px.pie(n_df, names='Asset', values='Pct', title="חשיפת נוסטרו", hole=0.3), use_container_width=True)

    with tabs[3]:
        st.subheader("⛈️ Stress Test: סימולטור רגישויות רגולטורי")
        s1, s2, s3 = st.columns(3)
        m_s = s1.slider("זעזוע מניות (%)", 0, 40, 0)
        i_s = s2.slider("שינוי ריבית (BPS)", -100, 100, 0)
        l_s = s3.slider("ביטולים (Lapse) %", 0, 20, 0)
        imp = (m_s * d['mkt_sens']) + (abs(i_s/100) * d['int_sens']) + (l_s * d['lapse_sens'])
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=max(0, d['solvency_ratio']-imp), title={'text': "סולבנסי חזוי"}, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 110], 'color': "red"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
else:
    st.error("נא לוודא שקובץ database.csv קיים.")
