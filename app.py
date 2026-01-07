import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. הגדרות דף ועיצוב Enterprise
st.set_page_config(page_title="GLOBAL INSIGHT PRO | Insurance AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e1e4e8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .main-header { font-size: 36px; color: #1a3a5a; font-weight: bold; text-align: right; }
    .sub-header { font-size: 20px; color: #4a5568; text-align: right; margin-bottom: 20px; }
    .formula-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-right: 5px solid #007bff; margin: 10px 0; direction: ltr; }
    </style>
    """, unsafe_allow_html=True)

# 2. טעינת נתונים חסינה (Data Persistence)
def load_data():
    paths = ['data/database.csv', 'database.csv']
    df = None
    for path in paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                break
            except: continue
    
    if df is None: # נתוני גיבוי למקרה שהקובץ לא נטען
        data = {
            'company': ['Phoenix', 'Harel'], 'year': [2025, 2025], 'quarter': ['Q3', 'Q3'],
            'solvency_ratio': [185, 172], 'csm_balance': [12.4, 11.8], 'loss_component': [150, 190],
            'roe': [14.2, 12.5], 'liquidity': [1.2, 1.3], 'combined_ratio': [92.5, 94.2],
            'life_csm': [6.5, 5.9], 'health_csm': [3.2, 2.9], 'general_csm': [2.7, 3.0],
            'int_sens': [0.14, 0.15], 'mkt_sens': [0.11, 0.10], 'tier1_ratio': [162, 152],
            'equity_to_balance': [8.4, 7.9], 'operating_cash_flow': [1.8, 1.5],
            'life_release_rate': [7.2, 7.5], 'health_release_rate': [9.1, 9.5], 'general_release_rate': [12.5, 13.0],
            'life_new_biz_strain': [3.1, 3.5], 'health_new_biz_strain': [5.2, 5.5], 'general_new_biz_strain': [8.4, 9.0],
            'csm_to_equity': [1.4, 1.2]
        }
        df = pd.DataFrame(data)
    return df

df = load_data()

# 3. תפריט צידי וניתוח AI
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/916/916771.png", width=100)
st.sidebar.title("🛡️ מערכת פיקוח AI")
company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
c_data = df[df['company'] == company].iloc[-1]

# כותרת
st.markdown(f"<div class='main-header'>Insurance Insight Pro: {company}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>ניתוח רגולטורי מתקדם | {c_data['quarter']} {c_data['year']}</div>", unsafe_allow_html=True)

# 🤖 AI Insights Executive Summary
st.subheader("🤖 AI Executive Insights")
c_col1, c_col2 = st.columns([1, 3])
with c_col1:
    resilience_score = (c_data['solvency_ratio']/2.5 + c_data['roe']*2) / 10
    st.metric("Resilience Score", f"{resilience_score:.1f}/100")
with c_col2:
    if c_data['solvency_ratio'] > df['solvency_ratio'].mean():
        st.success(f"ניתוח AI: {company} מציגה חוסן הוני גבוה מממוצע השוק. פוטנציאל חלוקת דיבידנד גבוה.")
    else:
        st.warning(f"ניתוח AI: יחס סולבנסי מתחת לממוצע העמיתים. נדרשת בחינה של נכסי הסיכון.")

st.divider()

# 4. מבנה הטאבים המשודרג
tabs = st.tabs(["📊 KPIs קריטיים", "🧬 עומק IFRS 17", "🏁 השוואת שוק", "🧪 Stress Test", "⚖️ דוח כספי"])

with tabs[0]: # KPIs
    st.subheader("חמשת מדדי הליבה [cite: 2026-01-03]")
    cols = st.columns(5)
    metrics = [
        ("Solvency Ratio", f"{c_data['solvency_ratio']}%", r"Ratio = \frac{Eligible\ Funds}{SCR}"),
        ("Total CSM", f"₪{c_data['csm_balance']}B", r"CSM_{t} = CSM_{t-1} + NB - Rel"),
        ("Loss Component", f"₪{c_data['loss_component']}M", "Onerous Contracts"),
        ("ROE", f"{c_data['roe']}%", r"ROE = \frac{Net\ Income}{Equity}"),
        ("Liquidity", f"{c_data['liquidity']}x", r"Ratio = \frac{Liquid\ Assets}{Liabilities}")
    ]
    for i, (name, val, form) in enumerate(metrics):
        with cols[i]:
            st.metric(name, val)
            with st.expander("מתודולוגיה"):
                st.latex(form)

with tabs[1]: # IFRS 17 Deep Dive
    st.subheader("ניתוח חיתומי לפי מגזרים")
    col_t, col_p = st.columns([2, 1])
    with col_t:
        seg_df = pd.DataFrame({
            "מדד": ["Release Rate", "New Business Strain"],
            "חיים": [f"{c_data['life_release_rate']}%", f"{c_data['life_new_biz_strain']}%"],
            "בריאות": [f"{c_data['health_release_rate']}%", f"{c_data['health_new_biz_strain']}%"],
            "כללי": [f"{c_data['general_release_rate']}%", f"{c_data['general_new_biz_strain']}%"]
        })
        st.table(seg_df)
    with col_p:
        fig_pie = px.pie(values=[c_data['life_csm'], c_data['health_csm'], c_data['general_csm']], 
                         names=['חיים', 'בריאות', 'כללי'], hole=0.4, title="פיזור CSM")
        st.plotly_chart(fig_pie, use_container_width=True)

with tabs[2]: # Benchmarking
    st.subheader("🏁 השוואת עמיתים (Benchmarking)")
    fig_bench = px.scatter(df, x="solvency_ratio", y="roe", size="csm_balance", color="company",
                           text="company", labels={"solvency_ratio": "חוסן", "roe": "רווחיות"})
    fig_bench.update_traces(textposition='top center')
    st.plotly_chart(fig_bench, use_container_width=True)
    st.info(f"מדד CSM/Equity: {c_data['csm_to_equity']}x (ממוצע שוק: {df['csm_to_equity'].mean():.2f}x)")

with tabs[3]: # Stress Test
    st.subheader("🧪 סימולציית תרחישי קיצון")
    s_mkt = st.slider("קריסת שוק המניות (%)", -40, 0, 0)
    impact = (s_mkt/10 * c_data['mkt_sens'] * 100)
    res_solv = c_data['solvency_ratio'] + impact
    
    st.metric("Solvency בתרחיש", f"{res_solv:.1f}%", f"{impact:.1f}%")
    fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=res_solv, 
        gauge={'axis': {'range': [0, 250]}, 'steps': [
            {'range': [0, 100], 'color': "red"}, {'range': [100, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]}))
    st.plotly_chart(fig_gauge, use_container_width=True)

with tabs[4]: # Financials
    st.subheader("ניתוח דוחות כספיים")
    f1, f2, f3 = st.columns(3)
    f1.metric("Combined Ratio", f"{c_data['combined_ratio']}%")
    f2.metric("Tier 1 Ratio", f"{c_data['tier1_ratio']}%")
    f3.metric("Equity to Balance", f"{c_data['equity_to_balance']}%")
    st.metric("Operating Cash Flow", f"₪{c_data['operating_cash_flow']}B")
