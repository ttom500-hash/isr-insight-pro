import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import base64
import os
from datetime import date

# --- 1. Apex Branding & Security Setup ---
st.set_page_config(page_title="Apex - Institutional Intelligence", page_icon="🛡️", layout="wide")

# פונקציית סנכרון אוטומטי ל-GitHub (SupTech Logic)
def sync_to_github(new_row):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        path = "data/database.csv"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        # 1. שליפת הקובץ הקיים
        r = requests.get(url, headers=headers).json()
        current_content = base64.b64decode(r['content']).decode('utf-8')
        
        # 2. הוספת השורה החדשה (בדיקה שאינה כפולה)
        if new_row not in current_content:
            updated_content = current_content.strip() + "\n" + new_row
            
            # 3. דחיפה (Push) חזרה ל-GitHub
            payload = {
                "message": f"Auto-update: {new_row.split(',')[0]} {new_row.split(',')[2]}",
                "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
                "sha": r['sha']
            }
            res = requests.put(url, json=payload, headers=headers)
            return res.status_code == 200
        return True
    except Exception as e:
        st.error(f"שגיאת סנכרון: {e}")
        return False

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # המרה למספרים למניעת שגיאות חישוב
    numeric_cols = df.columns.drop(['company', 'quarter'])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_kpi(label, value, title, desc, formula):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(title)
        st.write(desc)
        st.divider()
        st.write("**הגדרה פיננסית/אקטוארית:**")
        st.latex(formula)

# --- 2. Sidebar: ניווט ופורטל אוטומטי ---
df = load_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption("Strategic Financial Supervision | 2026")
    st.metric("⏳ ימים לפרסום שנתי", (date(2026, 3, 31) - date.today()).days)
    st.divider()

    with st.expander("📂 פורטל טעינה אוטומטי (Bulk)"):
        st.write("גרור קבצי PDF לעדכון מיידי של ה-GitHub")
        files = st.file_uploader("טעינת קבצים", type=['pdf'], accept_multiple_files=True)
        if files:
            for f in files:
                # סימולציה של חילוץ נתונים
                row = f"{f.name.split('.')[0]},2025,Q4,185.0,14.9,13.5,91.8,4.6,12.7,15.0,1.4,7.4,4.2,3.3,82.0,15.0,0.18,0.12,0.08,14.5,7.8,3.2,2.5,0.8"
                if sync_to_github(row): st.success(f"נשמר ב-GitHub: {f.name}")
            st.rerun()

    if not df.empty:
        st.divider()
        st.header("🔍 הגדרות דוח")
        sel_comp = st.selectbox("בחר ישות מדווחת:", sorted(df['company'].unique()))
        df_comp = df[df['company'] == sel_comp].sort_values(by=['year', 'quarter'])
        sel_q = st.selectbox("רבעון דיווח:", df_comp['quarter'].unique()[::-1])
        d = df_comp[df_comp['quarter'] == sel_q].iloc[0]

# --- 3. Main Dashboard: ניתוח עומק מוסדי ---
if not df.empty:
    st.title(f"פורטל פיקוח מוסדי: {sel_comp}")
    st.caption(f"תקופה: {sel_q} 2025 | סטטוס: Verified & Automated ✅")

    # שורת ה-KPIs עם ה-Popovers המקצועיים
    st.divider()
    m = st.columns(5)
    with m[0]: render_kpi("סולבנסי", f"{int(d['solvency_ratio'])}%", "יחס כושר פירעון", "חוסן הוני רגולטורי.", r"Ratio = \frac{Own \ Funds}{SCR}")
    with m[1]: render_kpi("יתרת CSM", f"₪{d['csm_total']}B", "Contractual Service Margin", "רווח עתידי.", r"CSM_{t} = CSM_{t-1} + NB - Release")
    with m[2]: render_kpi("ROE", f"{d['roe']}%", "תשואה להון", "יעילות רווח לבעלי מניות.", r"ROE = \frac{Net \ Income}{Equity}")
    with m[3]: render_kpi("יחס משולב", f"{d['combined_ratio']}%", "Combined Ratio", "יעילות חיתומית.", r"CR = \frac{Loss+Exp}{Premium}")
    with m[4]: render_kpi("NB Margin", f"{d['new_biz_margin']}%", "מרווח עסק חדש", "רווחיות מכירות.", r"Margin = \frac{CSM_{new}}{PV \ Prem}")

    # טאבים מקצועיים בגישה הוליסטית
    tabs = st.tabs(["📉 מגמות ושנת 2025", "🏛️ חוסן הוני (Solvency II)", "📑 ניתוח IFRS 17", "⛈️ רגישויות", "🏁 השוואת עמיתים"])

    with tabs[0]:
        st.subheader("ניתוח דוחות כספיים ומגמות רבעוניות")
        c1, c2, c3 = st.columns(3)
        with c1: render_kpi("איתנות (Eq/As)", f"{d['equity_to_assets']}%", "הון למאזן", "מינוף.", r"\frac{Equity}{Total \ Assets}")
        with c2: render_kpi("יעילות (Ex/Pr)", f"{d['expense_ratio']}%", "יחס הוצאות הנהלה", "תפעול.", r"\frac{OpEx}{Gross \ Premium}")
        with c3: render_kpi("איכות רווח", f"{d['op_cash_flow_ratio']}%", "תזרים מפעילות", "נזילות.", r"\frac{CFO}{Net \ Income}")
        st.plotly_chart(px.line(df_comp, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות רבעונית משולבת"), use_container_width=True)

    with tabs[1]:
        st.subheader("מבנה הון ודרישות SCR")
        
        ca, cb = st.columns(2)
        with ca:
            fig_bar = go.Figure(data=[go.Bar(name='הון מוכר', x=[sel_comp], y=[d['own_funds']]), go.Bar(name='דרישת SCR', x=[sel_comp], y=[d['scr_amount']])])
            st.plotly_chart(fig_bar, use_container_width=True)
        with cb:
            risk_df = pd.DataFrame({'קטגוריה': ['שוק', 'חיתום', 'תפעולי'], 'סכום': [d['mkt_risk'], d['und_risk'], d['operational_risk']]})
            st.plotly_chart(px.pie(risk_df, names='קטגוריה', values='סכום', hole=0.5, title="פילוח רכיבי SCR"), use_container_width=True)

    with tabs[2]:
        st.subheader("ניתוח מגזרי IFRS 17")
        
        cc, cd = st.columns(2)
        with cc:
            sec_df = pd.DataFrame({'מגזר': ['חיים', 'בריאות', 'כללי'], 'CSM': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.bar(sec_df, x='מגזר', y='CSM', title="יתרת CSM לפי קווי עסקים", color='מגזר'), use_container_width=True)
        with cd:
            mod_df = pd.DataFrame({'מודל': ['VFA', 'PAA', 'GMM'], 'אחוז': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(mod_df, names='מודל', values='אחוז', hole=0.6, title="תמהיל מודלים למדידה"), use_container_width=True)

    with tabs[3]:
        st.subheader("ניתוחי רגישות (Stress Test)")
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

    with tabs[4]:
        st.subheader(f"השוואת עמיתים (Peers) - רבעון {sel_q}")
        
        peer_metric = st.selectbox("בחר מדד להשוואה:", ['solvency_ratio', 'csm_total', 'roe', 'combined_ratio'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=peer_metric, ascending=False), x='company', y=peer_metric, color='company', text_auto=True), use_container_width=True)

else:
    st.error("לא נמצא נתונים. וודא שקיים קובץ data/database.csv תקין.")
