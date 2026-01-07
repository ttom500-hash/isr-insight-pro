import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
import os

# --- 1. הגדרות מותג וליבה (Apex Branding) ---
st.set_page_config(page_title="Apex - SupTech Intelligence", page_icon="🛡️", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        df = pd.read_csv(path)
        numeric_cols = ['solvency_ratio', 'csm_total', 'roe', 'combined_ratio', 'new_biz_margin', 'own_funds', 'scr_amount']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    return pd.DataFrame()

def metric_with_help(label, value, title, description, formula=None):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(title)
        st.write(description)
        if formula: st.latex(formula)

# --- 2. מנוע חילוץ PDF (מוסתר בסרגל הצד) ---
def process_pdf_portal(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = "".join([p.extract_text() or "" for p in pdf.pages[:10]])
    companies = ["הפניקס", "הראל", "מגדל", "כלל", "מנורה"]
    detected = next((c for c in companies if c in text), "חברה לא מזוהה")
    return {"company": detected}

# --- 3. סרגל צד (Sidebar) - המבנה המקורי ---
df = load_data()

with st.sidebar:
    st.title("🛡️ Apex Intelligence")
    st.caption("מערכת פיקוח הוליסטית | IFRS 17 & Solvency II")
    st.divider()
    
    # פורטל הטעינה - ממוקם בצד כדי לא להפריע לדאשבורד
    with st.expander("📂 פורטל טעינה משולחן העבודה"):
        pdf_file = st.file_uploader("גרור דוח PDF", type=['pdf'])
        if pdf_file:
            res = process_pdf_portal(pdf_file)
            st.success(f"זוהה דוח: {res['company']}")
            st.code(f"{res['company']},2025,Q3,175.0,155.0,12.5...", language="text")

    st.divider()
    if not df.empty:
        sel_comp = st.selectbox("בחר חברה:", sorted(df['company'].unique()))
        df_comp = df[df['company'] == sel_comp].sort_values(by=['year', 'quarter'])
        sel_year = st.selectbox("בחר שנה:", sorted(df_comp['year'].unique(), reverse=True))
        sel_q = st.selectbox("בחר רבעון:", sorted(df_comp[df_comp['year']==sel_year]['quarter'].unique(), reverse=True))
        
        d = df_comp[(df_comp['year'] == sel_year) & (df_comp['quarter'] == sel_q)].iloc[0]

# --- 4. התצוגה המרכזית (החזרת המבנה המקורי) ---
if not df.empty:
    st.title(f"דוח פיקוחי מאוחד: {sel_comp}")
    st.caption(f"תקופה: {sel_q} {sel_year} | גישה גלובלית")

    # חמשת ה-KPIs הקריטיים (החזרת ה-Layout המקורי)
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_with_help("סולבנסי", f"{d['solvency_ratio']}%", "יחס כושר פירעון", r"Ratio = \frac{Own \ Funds}{SCR}")
    with c2: st.metric("יתרת CSM", f"₪{d['csm_total']}B")
    with c3: st.metric("ROE", f"{d['roe']}%")
    with c4: st.metric("יחס משולב", f"{d['combined_ratio']}%")
    with c5: metric_with_help("מרווח עסקים חדשים", f"{d['new_biz_margin']}%", "New Business Margin", "הרווחיות של פוליסות חדשות שנמכרו.")

    # טאבים מקוריים + תוספת מגמות בסוף
    t1, t2, t3, t4 = st.tabs(["🏛️ חוסן הוני", "📑 IFRS 17 ומגזרים", "⛈️ Stress Test", "📈 ניתוח מגמות"])

    with t1:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_sol = go.Figure(data=[
                go.Bar(name='הון מוכר', x=[sel_comp], y=[d['own_funds']], marker_color='#2E86C1'),
                go.Bar(name='דרישת SCR', x=[sel_comp], y=[d['scr_amount']], marker_color='#CB4335')
            ])
            fig_sol.update_layout(title="מבנה הון (₪ מיליארד)", barmode='group')
            st.plotly_chart(fig_sol, use_container_width=True)
        with col_b:
            risk_df = pd.DataFrame({'סיכון': ['שוק', 'חיתום', 'תפעולי'], 'סכום': [d['mkt_risk'], d['und_risk'], d['operational_risk']]})
            st.plotly_chart(px.pie(risk_df, names='סיכון', values='סכום', title="פילוח דרישת הון", hole=0.4), use_container_width=True)

    with t2:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            s_df = pd.DataFrame({'Sector': ['חיים', 'בריאות', 'כללי'], 'Val': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.pie(s_df, names='Sector', values='Val', title="פילוח CSM מגזרי"), use_container_width=True)
        with col_c2:
            m_df = pd.DataFrame({'Model': ['VFA', 'PAA', 'GMM'], 'Share': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(m_df, names='Model', values='Share', title="תמהיל מודלים (IFRS 17)", hole=0.5), use_container_width=True)

    with t3:
        st.subheader("⛈️ סימולציית רגישות לשוק")
        shock = st.slider("זעזוע מניות (%)", 0, 40, 0)
        impact = shock * d['mkt_sens']
        new_solvency = max(0, d['solvency_ratio'] - impact)
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_solvency, title={'text': "סולבנסי חזוי"})), use_container_width=True)

    with t4:
        st.subheader("ניתוח מגמות רבעוני")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.plotly_chart(px.line(df_comp, x='quarter', y='solvency_ratio', markers=True, title="מגמת סולבנסי"), use_container_width=True)
        with col_t2:
            st.plotly_chart(px.line(df_comp, x='quarter', y='csm_total', markers=True, title="מגמת CSM (₪ מיליארד)"), use_container_width=True)
else:
    st.error("נא לוודא שקובץ database.csv נמצא בתיקיית data ב-GitHub.")
