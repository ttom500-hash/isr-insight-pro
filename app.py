import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות עיצוב
st.set_page_config(page_title="SupTech Insurance Analytics v2.0", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

df = load_data()

if not df.empty:
    st.sidebar.title("🔍 מערכת פיקוח SupTech")
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    company_data = df[df['company'] == selected_company].iloc[-1]

    # כותרת וציון ביטחון נתונים
    c_h, c_c = st.columns([3, 1])
    c_h.title(f"ניתוח עומק רגולטורי: {selected_company}")
    conf = 95 if company_data.get('data_source') == "AI_Verified" else 75
    c_c.metric("ביטחון נתונים AI", f"{conf}%")

    st.divider()

    # חמשת מדדי הזהב (Top 5 KPIs)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("יחס סולבנסי", f"{company_data.get('solvency_ratio', 0)}%")
    m2.metric("יתרת CSM", f"₪{company_data.get('csm_balance', 0)}B")
    m3.metric("תשואה להון (ROE)", f"{company_data.get('roe', 0)}%")
    m4.metric("Combined Ratio", f"{company_data.get('combined_ratio', 0)}%")
    m5.metric("נזילות", f"{company_data.get('liquidity', 0)}")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 KPIs ומגמות", "⚖️ השוואת שוק", "🏗️ נכסים והתחייבויות", "⛈️ Stress Test"])

    with tab1:
        st.subheader("מבנה רווחיות (IFRS 17)")
        col_pie, col_info = st.columns(2)
        with col_pie:
            # פילוח CSM מגזרי
            fig = px.pie(names=['חיים', 'בריאות', 'כללי'], 
                         values=[company_data.get('life_csm', 0), company_data.get('health_csm', 0), company_data.get('general_csm', 0)], 
                         title="פילוח CSM מגזרי (מיליארדי ש''ח)", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with col_info:
            st.info(f"נכסים מנוהלים בחוזי השקעה (AUM): ₪{company_data.get('inv_contracts_aum', 0)}B")
            st.write("מגזר זה מייצג פעילות חוץ-ביטוחית המניבה דמי ניהול קבועים.")

    with tab2:
        st.subheader("מיקום החברה מול השוק (Benchmarking)")
        # השוואה בין כל החברות ב-CSV
        fig_s = px.scatter(df, x="solvency_ratio", y="roe", size="csm_balance", color="company", text="company",
                           labels={"solvency_ratio": "חוסן הוני (%)", "roe": "רווחיות (%)"})
        st.plotly_chart(fig_s, use_container_width=True)

    with tab3:
        st.subheader("ניתוח חשיפה לנכסים ומודל VFA")
        ca, cb = st.columns(2)
        with ca:
            # גרף חשיפה לנכסי סיכון
            assets = pd.DataFrame({
                'נכס': ['נדל"ן', 'מניות', 'אלטרנטיבי'], 
                'חשיפה (%)': [company_data.get('re_pct', 0), company_data.get('equity_pct', 0), company_data.get('alts_pct', 0)]
            })
            st.plotly_chart(px.bar(assets, x='נכס', y='חשיפה (%)', color='נכס', title="חשיפה לנכסי סיכון (%)"), use_container_width=True)
        with cb:
            # מודל VFA מול GMM
            vfa = company_data.get('vfa_pct', 0)
            st.plotly_chart(px.pie(names=['משתתפות (VFA)', 'רגיל'], values=[vfa, 100-vfa], 
                                   title="מבנה CSM: מודל VFA מול רגיל", hole=0.5), use_container_width=True)

    with tab4:
        st.subheader("⛈️ Stress Test: סימולציית רגישויות")
        m_s = st.slider("קריסת בורסה (%)", 0, 40, 0)
        i_s = st.slider("עליית ריבית (BPS)", -100, 100, 0)
        l_s = st.slider("ביטולים (%)", 0, 20, 0)
        
        # נוסחת השפעה רגולטורית
        impact = (m_s * company_data.get('mkt_sens', 0)) + \
                 (abs(i_s/100) * company_data.get('int_sens', 0)) + \
                 (l_s * company_data.get('lapse_sens', 0))
        
        new_sol = max(0, company_data.get('solvency_ratio', 0) - impact)
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=new_sol, title={'text': "סולבנסי חזוי תחת לחץ"},
            gauge={'axis': {'range': [0, 250]}, 
                   'steps': [{'range': [0, 110], 'color': "red"}, 
                             {'range': [110, 150], 'color': "orange"}, 
                             {'range': [150, 250], 'color': "green"}]}))
        st.plotly_chart(fig_gauge, use_container_width=True)
else:
    st.warning("מחכה להזנת נתונים ל-database.csv...")
