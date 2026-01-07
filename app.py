import streamlit as st
import pandas as pd
import pdfplumber
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import date

# --- 1. Apex Branding & Config ---
st.set_page_config(page_title="Apex - SupTech Intelligence", page_icon="🛡️", layout="wide")

def get_countdown():
    deadline = date(2026, 3, 31)
    return max(0, (deadline - date.today()).days)

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        df = pd.read_csv(path)
        # המרה בטוחה למספרים למניעת באגים
        numeric_cols = ['solvency_ratio', 'csm_total', 'roe', 'combined_ratio', 'own_funds', 'scr_amount', 'mkt_sens']
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

# --- 2. מנוע חילוץ PDF (עבור התיקיות בשולחן העבודה) ---
def process_pdf_portal(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "".join([p.extract_text() or "" for p in pdf.pages[:15]])
        companies = ["הפניקס", "הראל", "מגדל", "כלל", "מנורה"]
        detected = next((c for c in companies if c in text), "חברה לא מזוהה")
        return {"company": detected, "found": True}
    except:
        return {"found": False}

# --- 3. Sidebar: Navigation & Portal ---
df = load_data()
with st.sidebar:
    st.title("🛡️ Apex Intelligence")
    st.caption("מערכת פיקוח הוליסטית | IFRS 17 & Solvency II")
    
    st.divider()
    st.subheader("📂 פורטל טעינת דוחות")
    st.info("גרור PDF מתיקיית הדיווחים שלך")
    pdf_file = st.file_uploader("טעינה משולחן העבודה", type=['pdf'])
    
    if pdf_file:
        res = process_pdf_portal(pdf_file)
        if res["found"]:
            st.success(f"זוהה דוח: {res['company']}")
            if st.button("הכן שורה למחסן"):
                st.code(f"{res['company']},2025,Q3,175.0,155.0,12.5,80.0,15.0,12.5,92.0...", language="text")
                st.info("העתק והוסף ל-database.csv בתיקיית Data_Warehouse")

    st.divider()
    if not df.empty:
        st.header("🔍 מנוע חיפוש")
        sel_comp = st.selectbox("1. בחר חברה:", sorted(df['company'].unique()))
        available_years = sorted(df[df['company'] == sel_comp]['year'].unique(), reverse=True)
        sel_year = st.selectbox("2. בחר שנה:", available_years)
        available_quarters = sorted(df[(df['company'] == sel_comp) & (df['year'] == sel_year)]['quarter'].unique(), reverse=True)
        sel_q = st.selectbox("3. בחר רבעון:", available_quarters)
        
        # שליפת נתוני רבעון נבחר
        d = df[(df['company']==sel_comp) & (df['year']==sel_year) & (df['quarter']==sel_q)].iloc[0]
        # שליפת כל נתוני החברה (עבור גרפי מגמה)
        df_comp = df[df['company'] == sel_comp].sort_values(by=['year', 'quarter'])

# --- 4. Main Dashboard ---
if not df.empty:
    st.title(f"דוח פיקוחי מאוחד: {sel_comp}")
    st.caption(f"תקופה: {sel_q} {sel_year} | מערכת Apex | מבוסס נתוני תיקייה")

    # שורת ה-KPIs המרכזית (לפי הצ'קליסט)
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_with_help("סולבנסי", f"{d['solvency_ratio']}%", "יחס כושר פירעון", r"Ratio = \frac{Own \ Funds}{SCR}")
    with c2: st.metric("יתרת CSM", f"₪{d['csm_total']}B")
    with c3: st.metric("ROE (תשואה להון)", f"{d['roe']}%")
    with c4: metric_with_help("יחס משולב", f"{d['combined_ratio']}%", "רווחיות חיתומית", "סה\"כ הפסדים והוצאות מול פרמיות")

    # טאבים מפורטים
    tabs = st.tabs(["📈 ניתוח מגמות רבעוני", "🏛️ חוסן הוני (Solvency)", "📑 IFRS 17 ומגזרים", "⛈️ Stress Test"])

    with tabs[0]:
        st.subheader(f"התפתחות רבעונית - {sel_comp}")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_trend_sol = px.line(df_comp, x='quarter', y='solvency_ratio', markers=True, title="מגמת יחס סולבנסי")
            fig_trend_sol.update_traces(line_color='#2E86C1', line_width=4)
            st.plotly_chart(fig_trend_sol, use_container_width=True)
        with col_t2:
            fig_trend_csm = px.line(df_comp, x='quarter', y='csm_total', markers=True, title="מגמת יתרת CSM (₪ מיליארד)")
            fig_trend_csm.update_traces(line_color='#28B463', line_width=4)
            st.plotly_chart(fig_trend_csm, use_container_width=True)

    with tabs[1]:
        
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

    with tabs[2]:
        
        st.subheader("ניתוח מגזרי ושיטות מדידה")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            s_df = pd.DataFrame({'Sector': ['חיים', 'בריאות', 'כללי'], 'Val': [d['life_csm'], d['health_csm'], d['general_csm']]})
            st.plotly_chart(px.pie(s_df, names='Sector', values='Val', title="פילוח CSM מגזרי"), use_container_width=True)
        with col_c2:
            m_df = pd.DataFrame({'Model': ['VFA', 'PAA', 'GMM'], 'Share': [d['vfa_csm_pct'], d['paa_pct'], 100-(d['vfa_csm_pct']+d['paa_pct'])]})
            st.plotly_chart(px.pie(m_df, names='Model', values='Share', title="תמהיל מודלים", hole=0.5), use_container_width=True)

    with tabs[3]:
        st.subheader("⛈️ Stress Test: סימולציית רגישות")
        shock = st.slider("זעזוע מניות (%)", 0, 40, 0)
        impact = shock * d['mkt_sens']
        new_solvency = max(0, d['solvency_ratio'] - impact)
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_solvency, title={'text': "סולבנסי חזוי"},
                                               gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 110], 'color': "red"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
else:
    st.error("נא לוודא שקובץ database.csv תקין ב-GitHub.")
