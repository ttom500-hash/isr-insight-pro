import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות עמוד RTL
st.set_page_config(page_title="מערכת פיקוח SupTech - גרסה סופית", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

df = load_data()

if not df.empty:
    st.sidebar.title("🔍 מרכז בקרה ופיקוח")
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    d = df[df['company'] == selected_company].iloc[-1]

    st.title(f"דוח פיננסי מעמיק: {selected_company} - Q3 2025")
    st.write(f"סטטוס תיקוף נתונים: **{d['data_source']}** | תקן דיווח: **IFRS 17 / Solvency II**")
    
    st.divider()

    # סקירת על - KPIs
    m_a, m_b, m_c, m_d = st.columns(4)
    m_a.metric("יחס כושר פירעון", f"{d['solvency_ratio']}%")
    m_b.metric("מרווח שירות (CSM)", f"₪{d['csm_total']}B")
    m_c.metric("סך נכסים מנוהלים (AUM)", f"₪{round(d['vfa_assets_aum'] + d['inv_contracts_aum'] + d['pension_aum'] + d['provident_aum'], 1)}B")
    m_d.metric("תשואה להון (ROE)", f"{d['roe']}%")

    # טאבים מקצועיים
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📑 ניתוח IFRS 17", 
        "💰 ניתוח AUM ונכסים", 
        "📈 יחסים פיננסיים",
        "⚖️ השוואה ענפית",
        "🌩️ מבחני קיצון (Stress Test)"
    ])

    with tab1:
        st.subheader("ניתוח מרווח שירות חוזי ומודל המדידה")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(names=['ביטוח חיים', 'ביטוח בריאות', 'ביטוח כללי'], 
                                   values=[d['life_csm'], d['health_csm'], d['general_csm']], 
                                   title="פילוח CSM לפי מגזרים (מיליארדי ש''ח)", hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(names=['גישת העמלה המשתנה (VFA)', 'מודל המדידה הכללי (GMM)'], 
                                   values=[d['vfa_csm_pct'], 100-d['vfa_csm_pct']], 
                                   title="שיטת מדידת התחייבויות ביטוחיות", hole=0.5,
                                   color_discrete_sequence=['#FFD700', '#ADD8E6']), use_container_width=True)

    with tab2:
        st.subheader("פילוח נכסים מנוהלים (AUM) וחשיפת נוסטרו")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            aum_data = pd.DataFrame({
                'מגזר': ['פנסיה', 'גמל', 'חוזי השקעה', 'נכסי VFA'],
                'מיליארדי ש"ח': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]
            })
            st.plotly_chart(px.bar(aum_data, x='מגזר', y='מיליארדי ש"ח', color='מגזר', text='מיליארדי ש"ח',
                                   title="נכסים מנוהלים לפי קטגוריות דיווח"), use_container_width=True)
        with col_b:
            assets = pd.DataFrame({'נכס': ['נדל"ן', 'מניות', 'אלטרנטיבי'], 
                                   'חשיפה (%)': [d['re_pct'], d['equity_pct'], d['alts_pct']]})
            st.plotly_chart(px.pie(assets, names='נכס', values='חשיפה (%)', hole=0.3, title="חשיפת נוסטרו"), use_container_width=True)

    with tab3:
        st.subheader("ניתוח יחסים פיננסיים רגולטוריים")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.write("**📊 יחסי מאזן**")
            st.latex(r"Equity \ Ratio = \frac{Total \ Equity}{Total \ Assets}")
            st.metric("הון עצמי לסך מאזן", f"{d['equity_to_assets']}%")
            st.metric("יחס הון רובד 1", f"{d['tier1_ratio']}%")
        with r2:
            st.write("**💰 יחסי רווח והפסד**")
            st.latex(r"Expense \ Ratio = \frac{Op \ Expenses}{Gross \ Premiums}")
            st.metric("יחס הוצאות הנהלה וכלליות", f"{d['expense_ratio']}%")
            st.metric("יחס תביעות (Claims Ratio)", f"{d['claims_ratio']}%")
        with r3:
            st.write("**💸 יחסי תזרים**")
            st.latex(r"CF \ Ratio = \frac{Operating \ Cash \ Flow}{Net \ Profit}")
            st.metric("יחס תזרים מפעילות שוטפת", f"{d['op_cash_flow_ratio']}")
            st.metric("יחס נזילות שוטפת", f"{d['liquidity']}")

    with tab4:
        st.subheader("מיקום החברה במפת הסיכון הענפית")
        st.plotly_chart(px.scatter(df, x="solvency_ratio", y="roe", size="csm_total", color="company", text="company",
                                   labels={"solvency_ratio": "יחס כושר פירעון (%)", "roe": "ROE (%)"},
                                   title="חוסן הוני (Solvency) מול רווחיות (ROE)"), use_container_width=True)

    with tab5:
        st.subheader("🌩️ Stress Test: מבחני רגישות משולבים")
        s1, s2, s3 = st.columns(3)
        m_s = s1.slider("זעזוע שוק המניות (%)", 0, 40, 0)
        i_s = s2.slider("שינוי בעקום הריבית (BPS)", -100, 100, 0)
        l_s = s3.slider("עלייה בשיעור ביטולים (Lapse) %", 0, 20, 0)
        
        impact = (m_s * d['mkt_sens']) + (abs(i_s/100) * d['int_sens']) + (l_s * d['lapse_sens'])
        new_sol = max(0, d['solvency_ratio'] - impact)
        
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_sol, 
                                               title={'text': "יחס כושר פירעון חזוי תחת לחץ"},
                                               gauge={'axis': {'range': [0, 250]},
                                                      'steps': [{'range': [0, 110], 'color': "red"}, 
                                                                {'range': [110, 150], 'color': "orange"}, 
                                                                {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
        if l_s > 0:
            st.warning(f"תרחיש הביטולים גרע {round(l_s * d['lapse_sens'], 2)}% מיחס ההון.")
else:
    st.error("נא להזין נתונים רשמיים לקובץ database.csv.")
