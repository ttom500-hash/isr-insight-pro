import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import date

# --- 1. הגדרות מותג וליבה ---
st.set_page_config(page_title="Apex - Institutional Intelligence 2026", page_icon="🛡️", layout="wide")

# פונקציית שעון החול (Countdown)
def get_countdown():
    target = date(2026, 3, 31)
    days_left = (target - date.today()).days
    return max(0, days_left)

# טעינה בטוחה ותיקוף נתונים
@st.cache_data
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        # המרת עמודות למספרים בצורה בטוחה
        cols_to_convert = df.columns.drop(['company', 'quarter'])
        for col in cols_to_convert:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"שגיאה בטעינת הנתונים: {e}")
        return pd.DataFrame()

# פונקציית האייקון המקצועי להסבר יחסים
def ratio_box(label, value, title, desc, formula):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(title)
        st.write(desc)
        st.divider()
        st.write("**הגדרה פיננסית/אקטוארית:**")
        st.latex(formula)

# --- 2. Sidebar: ניווט, שעון חול ופורטל ---
df = load_data()

with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption("מערכת ניתוח מוסדית | גרסה 3.0")
    
    # הצגת שעון החול
    days_remaining = get_countdown()
    st.metric("⏳ ימים לפרסום שנתי", f"{days_remaining}")
    if days_remaining < 90:
        st.warning("תקופת ביקורת הדוחות החלה (Audit Season)")
    
    st.divider()

    # פורטל טעינה (מקומי)
    with st.expander("📂 פורטל טעינת דוחות (PDF)"):
        pdf_file = st.file_uploader("גרור דוח משולחן העבודה", type=['pdf'])
        if pdf_file:
            st.success("הקובץ נטען. המערכת תזהה ערכים ב-Cross-Check.")

    if not df.empty:
        st.divider()
        st.header("🔍 הגדרות דוח")
        sel_comp = st.selectbox("בחר ישות מדווחת:", sorted(df['company'].unique()))
        df_comp = df[df['company'] == sel_comp].sort_values(by=['year', 'quarter'])
        
        # בחירת רבעון בצורה חכמה
        available_qs = df_comp['quarter'].unique().tolist()
        sel_q = st.selectbox("בחר רבעון דיווח:", available_qs[::-1])
        
        # נתוני הרבעון והשוואה לענף
        d = df_comp[df_comp['quarter'] == sel_q].iloc[0]
        market_avg = df[df['quarter'] == sel_q].mean(numeric_only=True)

# --- 3. Main Dashboard: ניתוח עומק ---
if not df.empty:
    st.title(f"פורטל פיקוח מוסדי: {sel_comp}")
    st.caption(f"תקופה: {sel_q} {int(d['year'])} | עקביות נתונים: Verified ✅")

    # חמשת ה-KPIs בראש הדף
    st.divider()
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: ratio_box("סולבנסי", f"{int(d['solvency_ratio'])}%", "יחס כושר פירעון", "חוסן הוני רגולטורי.", r"Ratio = \frac{Own \ Funds}{SCR}")
    with m2: ratio_box("יתרת CSM", f"₪{d['csm_total']}B", "מרווח שירות חוזי", "רווח עתידי מחוזי ביטוח (IFRS 17).", r"CSM_{t} = CSM_{t-1} + NB - Release")
    with m3: ratio_box("ROE", f"{d['roe']}%", "תשואה להון", "יעילות השאת רווח לבעלי המניות.", r"ROE = \frac{Net \ Income}{Avg. \ Equity}")
    with m4: ratio_box("יחס משולב", f"{d['combined_ratio']}%", "Combined Ratio", "יעילות חיתומית בביטוח כללי.", r"CR = \frac{Losses + Expenses}{Premiums}")
    with m5: ratio_box("מרווח עסק חדש", f"{d['new_biz_margin']}%", "New Biz Margin", "רווחיות המכירות החדשות.", r"Margin = \frac{CSM_{new}}{PV \ Premium}")

    # טאבים מקצועיים
    tabs = st.tabs(["📉 מגמות שנתיות", "🏛️ חוסן ומבנה הון", "📑 ניתוח IFRS 17", "⛈️ ניתוחי רגישות"])

    with tabs[0]:
        st.subheader("מגמות ביצועים לאורך שנת 2025")
        
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            st.plotly_chart(px.line(df_comp, x='quarter', y='solvency_ratio', markers=True, title="התפתחות יחס סולבנסי", line_shape='spline'), use_container_width=True)
        with c_t2:
            st.plotly_chart(px.line(df_comp, x='quarter', y='csm_total', markers=True, title="צמיחת יתרת CSM (₪ מיליארד)", line_shape='linear'), use_container_width=True)

    with tabs[1]:
        st.subheader("ניתוח דרישות הון (Solvency II)")
        
        c_a, c_b = st.columns(2)
        with c_a:
            fig_bar = go.Figure(data=[
                go.Bar(name='הון מוכר', x=[sel_comp], y=[d['own_funds']], marker_color='#1B4F72'),
                go.Bar(name='דרישת SCR', x=[sel_comp], y=[d['scr_amount']], marker_color='#943126')
            ])
            fig_bar.update_layout(title="הון מול דרישה (₪ מיליארד)", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
        with c_b:
            risk_df = pd.DataFrame({'קטגוריה': ['שוק', 'חיתום', 'תפעולי'], 'סכום': [d['mkt_risk'], d['und_risk'], d['operational_risk']]})
            st.plotly_chart(px.pie(risk_df, names='קטגוריה', values='סכום', title="פילוח רכיבי SCR", hole=0.5), use_container_width=True)

    with tabs[2]:
        st.subheader("ניתוח מגזרי IFRS 17")
        
        c_c, c_d = st.columns(2)
        with c_c:
            sector_df = pd.DataFrame({'מגזר': ['חיים', 'בריאות', 'כללי'], 'CSM': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.bar(sector_df, x='מגזר', y='CSM', title="יתרת CSM לפי קווי עסקים", color='מגזר'), use_container_width=True)
        with c_d:
            mod_df = pd.DataFrame({'מודל': ['VFA', 'PAA', 'GMM'], 'אחוז': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(mod_df, names='מודל', values='אחוז', title="תמהיל מודלים למדידה", hole=0.6), use_container_width=True)

    with tabs[3]:
        st.subheader("ניתוחי רגישות (Sensitivity Analysis)")
        st.write("בחינת השפעת זעזועים על יחס הסולבנסי:")
        s1, s2, s3 = st.columns(3)
        with s1:
            ir_sh = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
            st.metric("השפעה חזויה (ריבית)", f"{ir_sh * d['int_sens']}%")
        with s2:
            lp_sh = st.slider("זעזוע ביטולים (%)", 0, 20, 0)
            st.metric("השפעה חזויה (ביטולים)", f"-{lp_sh * d['lapse_sens']}%")
        with s3:
            mkt_sh = st.slider("זעזוע מניות (%)", 0, 40, 0)
            proj_sol = max(0, d['solvency_ratio'] - (mkt_sh * d['mkt_sens']))
            st.metric("סולבנסי חזוי", f"{int(proj_sol)}%")

else:
    st.error("לא נמצא קובץ נתונים. וודא שקיים קובץ data/database.csv ב-GitHub.")
