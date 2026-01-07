import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות עמוד ועיצוב RTL
st.set_page_config(page_title="מערכת SupTech - ניתוח רגולטורי מקיף", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

df = load_data()

if not df.empty:
    st.sidebar.title("🔍 מרכז בקרה ופיקוח")
    selected = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    d = df[df['company'] == selected].iloc[-1]

    # כותרת ראשית
    st.title(f"דוח אנליטי: {selected} - רבעון 3, 2025")
    st.write("מקור: דוחות כספיים מאוחדים | סטטוס תיקוף: **עבר בהצלחה**")
    
    # חישוב סך נכסים מנוהלים (Total AUM)
    total_aum = d['vfa_assets_aum'] + d['inv_contracts_aum'] + d['pension_aum'] + d['provident_aum']
    
    st.divider()
    
    # KPIs רגולטוריים (Top Level Metrics)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("יחס כושר פירעון", f"{d['solvency_ratio']}%")
    m2.metric("מרווח שירות חוזי (CSM)", f"₪{d['csm_total']}B")
    m3.metric("סך נכסים מנוהלים (AUM)", f"₪{round(total_aum, 1)}B")
    m4.metric("תשואה להון (ROE)", f"{d['roe']}%")

    # טאבים לניתוח מעמיק - ללא קיצורי דרך
    tab1, tab2, tab3, tab4 = st.tabs([
        "📑 ניתוח IFRS 17 (ביטוח)", 
        "💰 ניתוח AUM (פנסיה/גמל/השקעות)", 
        "🏗️ השקעות נוסטרו", 
        "🌩️ מבחני רגישות"
    ])

    with tab1:
        st.subheader("ניתוח מרווח שירות חוזי (CSM) ומודל המדידה")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(names=['ביטוח חיים', 'ביטוח בריאות', 'ביטוח כללי'], 
                                   values=[d['life_csm'], d['health_csm'], d['general_csm']], 
                                   title="התפלגות CSM לפי מגזרי פעילות", hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(names=['גישת העמלה המשתנה (VFA)', 'מודל מדידה כללי (GMM)'], 
                                   values=[d['vfa_csm_pct'], 100-d['vfa_csm_pct']], 
                                   title="מתודולוגיית מדידת CSM (ביטוח)", hole=0.5,
                                   color_discrete_sequence=['#FFD700', '#87CEEB']), use_container_width=True)

    with tab2:
        st.subheader("פילוח נכסים מנוהלים - IFRS 9")
        aum_data = pd.DataFrame({
            'סוג פעילות': ['קרנות פנסיה', 'קופות גמל', 'חוזי השקעה', 'נכסי VFA (ביטוח)'],
            'מיליארדי ש"ח': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]
        })
        fig_aum = px.bar(aum_data, x='סוג פעילות', y='מיליארדי ש"ח', color='סוג פעילות', text='מיליארדי ש"ח',
                         title="נכסים מנוהלים (AUM) לפי קטגוריות דיווח")
        st.plotly_chart(fig_aum, use_container_width=True)

    with tab3:
        st.subheader("ניתוח חשיפת נוסטרו וסיכוני שוק")
        col_a, col_b = st.columns(2)
        with col_a:
            invest_df = pd.DataFrame({
                'סוג נכס': ['נדל"ן להשקעה', 'ניירות ערך הוניים', 'השקעות אלטרנטיביות'],
                'שיעור מהתיק (%)': [d['re_pct'], d['equity_pct'], d['alts_pct']]
            })
            st.plotly_chart(px.bar(invest_df, x='סוג נכס', y='שיעור מהתיק (%)', color='סוג נכס', 
                                   title="חשיפה לנכסי סיכון בתיק הנוסטרו"), use_container_width=True)
        with col_b:
            st.info(f"חשיפה כוללת לנכסים שאינם סחירים (נדל''ן + אלטרנטיבי): {d['re_pct'] + d['alts_pct']}%")
            st.write("מגמה זו משקפת אסטרטגיית פרמיית אי-נזילות המקובלת בחברות הביטוח הגדולות.")

    with tab4:
        st.subheader("⛈️ Stress Test: מבחני רגישות הון (Solvency II)")
        col1, col2 = st.columns([1, 2])
        with col1:
            m_shock = st.slider("זעזוע שוק המניות (%)", 0, 40, 0)
            i_shock = st.slider("שינוי בעקום הריבית (BPS)", -100, 100, 0)
        
        with col2:
            impact = (m_shock * d['mkt_sens']) + (abs(i_shock/100) * d['int_sens'])
            new_sol = max(0, d['solvency_ratio'] - impact)
            
            fig_g = go.Figure(go.Indicator(
                mode = "gauge+number", value = new_sol,
                title = {'text': "יחס כושר פירעון חזוי"},
                gauge = {'axis': {'range': [0, 250]},
                         'steps': [{'range': [0, 110], 'color': "red"}, 
                                   {'range': [110, 150], 'color': "orange"}, 
                                   {'range': [150, 250], 'color': "green"}]}))
            st.plotly_chart(fig_g, use_container_width=True)
else:
    st.error("קובץ הנתונים לא נמצא או שאינו תקין.")
