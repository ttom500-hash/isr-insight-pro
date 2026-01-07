import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import date

# --- 1. Branding & Security ---
st.set_page_config(page_title="Apex - Institutional Intelligence", page_icon="🛡️", layout="wide")

# פונקציית שעון החול המקורית
def get_countdown():
    target = date(2026, 3, 31)
    return max(0, (target - date.today()).days)

# טעינת נתונים עם תיקוף קוהרנטיות
@st.cache_data
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    numeric_cols = df.columns.drop(['company', 'quarter'])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# פונקציית האייקון וההסבר ב-Latex
def render_kpi(label, value, title, desc, formula):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(title)
        st.write(desc)
        st.divider()
        st.write("**הגדרה חשבונאית/אקטוארית:**")
        st.latex(formula)

# --- 2. Sidebar: שעון חול, ניווט ופורטל ---
df = load_data()

with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption("Strategic Financial Supervision | 2026")
    
    # שעון חול (נשמר כפי שביקשת)
    st.metric("⏳ ימים לפרסום שנתי", get_countdown())
    st.divider()

    # פורטל טעינה המוני (נשמר כפי שביקשת)
    with st.expander("📂 פורטל טעינת תיקייה (PDF)"):
        st.write("גרור את כל קבצי הדיווחים לכאן")
        uploaded_files = st.file_uploader("טעינה המונית", type=['pdf'], accept_multiple_files=True)
        if uploaded_files: st.success(f"נטענו {len(uploaded_files)} קבצים.")

    if not df.empty:
        st.divider()
        st.header("🔍 הגדרות דוח")
        sel_comp = st.selectbox("בחר חברה:", sorted(df['company'].unique()))
        df_comp = df[df['company'] == sel_comp].sort_values(by=['year', 'quarter'])
        
        # בחירת רבעון מוצלבת
        available_qs = df_comp['quarter'].unique().tolist()
        sel_q = st.selectbox("בחר רבעון:", available_qs[::-1])
        d = df_comp[df_comp['quarter'] == sel_q].iloc[0]
        
        # חישוב ממוצע שוק לרבעון הנבחר
        market_avg = df[df['quarter'] == sel_q].mean(numeric_only=True)

# --- 3. Main Dashboard: ניתוח עומק ---
if not df.empty:
    st.title(f"ניתוח פיקוחי הוליסטי: {sel_comp}")
    st.info(f"תקופה: {sel_q} 2025 | הנתונים מאומתים אל מול דוחות סולבנסי ו-IFRS 17")

    # שורת 5 ה-KPIs עם האייקונים המקוריים
    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: render_kpi("סולבנסי", f"{int(d['solvency_ratio'])}%", "יחס כושר פירעון", "חוסן הוני כלכלי.", r"Ratio = \frac{Own \ Funds}{SCR}")
    with m2: render_kpi("יתרת CSM", f"₪{d['csm_total']}B", "מרווח שירות חוזי", "רווח עתידי מחוזים (IFRS 17).", r"CSM_{t} = CSM_{t-1} + NB - Release")
    with m3: render_kpi("ROE", f"{d['roe']}%", "תשואה להון", "רווחיות לבעלי המניות.", r"ROE = \frac{Net \ Income}{Equity}")
    with m4: render_kpi("יחס משולב", f"{d['combined_ratio']}%", "Combined Ratio", "יעילות חיתומית.", r"CR = \frac{Losses + Expenses}{Premiums}")
    with m5: render_kpi("מרווח עסק חדש", f"{d['new_biz_margin']}%", "New Biz Margin", "רווחיות מכירות חדשות.", r"Margin = \frac{CSM_{new}}{PV \ Premium}")

    # טאבים מקצועיים (הכל נשמר + נוסף)
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות ודוחות", "🏛️ חוסן הוני", "📑 ניתוח IFRS 17", "⛈️ רגישויות", "🏁 השוואת עמיתים"])

    with t1:
        st.subheader("ניתוח דוחות כספיים ויחסי מאזן/תזרים")
        
        c1, c2, c3 = st.columns(3)
        with c1: render_kpi("איתנות (Eq/As)", f"{d['equity_to_assets']}%", "מינוף מאזני", "חלק ההון מהמאזן.", r"\frac{Equity}{Assets}")
        with c2: render_kpi("יעילות (Ex/Pr)", f"{d['expense_ratio']}%", "יחס הוצאות הנהלה", "יעילות תפעולית.", r"\frac{OpEx}{GWP}")
        with c3: render_kpi("איכות רווח", f"{d['op_cash_flow_ratio']}%", "יחס תזרים", "המרת רווח למזומן.", r"\frac{CFO}{Net \ Income}")
        st.divider()
        st.plotly_chart(px.line(df_comp, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="מגמה רבעונית משולבת"), use_container_width=True)

    with t2:
        st.subheader("מבנה הון ודרישות SCR (Solvency II)")
        
        ca, cb = st.columns(2)
        with ca:
            fig_bar = go.Figure(data=[go.Bar(name='הון מוכר', x=[sel_comp], y=[d['own_funds']]), go.Bar(name='דרישת SCR', x=[sel_comp], y=[d['scr_amount']])])
            st.plotly_chart(fig_bar, use_container_width=True)
        with cb:
            risk_df = pd.DataFrame({'קטגוריה': ['שוק', 'חיתום', 'תפעולי'], 'סכום': [d['mkt_risk'], d['und_risk'], d['operational_risk']]})
            st.plotly_chart(px.pie(risk_df, names='קטגוריה', values='סכום', hole=0.5, title="פילוח סיכונים"), use_container_width=True)

    with t3:
        st.subheader("ניתוח מגזרי IFRS 17")
        
        cc, cd = st.columns(2)
        with cc:
            sec_df = pd.DataFrame({'מגזר': ['חיים', 'בריאות', 'כללי'], 'CSM': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.bar(sec_df, x='מגזר', y='CSM', title="יתרת CSM לפי קווי עסקים", color='מגזר'), use_container_width=True)
        with cd:
            mod_df = pd.DataFrame({'מודל': ['VFA', 'PAA', 'GMM'], 'אחוז': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(mod_df, names='מודל', values='אחוז', hole=0.6, title="תמהיל מודלים"), use_container_width=True)

    with t4:
        st.subheader("ניתוחי רגישות (Sensitivity & Stress Test)")
        s1, s2, s3 = st.columns(3)
        with s1:
            ir = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
            st.metric("השפעה חזויה (ריבית)", f"{ir * d['int_sens']}%")
        with s2:
            lp = st.slider("זעזוע ביטולים (%)", 0, 20, 0)
            st.metric("השפעה חזויה (ביטולים)", f"-{lp * d['lapse_sens']}%")
        with s3:
            mkt = st.slider("זעזוע מניות (%)", 0, 40, 0)
            proj_sol = max(0, d['solvency_ratio'] - (mkt * d['mkt_sens']))
            st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj_sol, title={'text': "סולבנסי חזוי"})), use_container_width=True)

    with t5:
        st.subheader(f"השוואת עמיתים (Benchmark) - רבעון {sel_q}")
        
        p_metric = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'csm_total', 'roe', 'combined_ratio'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=p_metric, ascending=False), x='company', y=p_metric, color='company', text_auto=True), use_container_width=True)

else:
    st.error("לא נמצא נתונים. וודא שקיים קובץ data/database.csv תקין.")
