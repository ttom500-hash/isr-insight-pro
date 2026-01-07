import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות תצוגה
st.set_page_config(page_title="מערכת SupTech - ניתוח פיננסי מלא v3.5", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

df = load_data()

if not df.empty:
    st.sidebar.title("🔍 מרכז בקרה ופיקוח")
    selected = st.sidebar.selectbox("בחר חברה לניתוח מעמיק:", df['company'].unique())
    d = df[df['company'] == selected].iloc[-1]

    # כותרת ראשית
    st.title(f"דוח פיננסי ואנליטי: {selected} - Q3 2025")
    st.write(f"תקן דיווח: **IFRS 17 & Solvency II** | סטטוס אימות: {d['data_source']}")

    st.divider()

    # מדדי זהב (Top KPIs)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("יחס כושר פירעון", f"{d['solvency_ratio']}%")
    k2.metric("מרווח שירות חוזי (CSM)", f"₪{d['csm_total']}B")
    total_aum = d['vfa_assets_aum'] + d['inv_contracts_aum'] + d['pension_aum'] + d['provident_aum']
    k3.metric("סך נכסים מנוהלים (AUM)", f"₪{round(total_aum, 1)}B")
    k4.metric("תשואה להון (ROE)", f"{d['roe']}%")

    # טאבים מקצועיים
    tabs = st.tabs([
        "📑 ניתוח IFRS 17 (ביטוח)", 
        "💰 ניתוח AUM ונכסים", 
        "📈 יחסים פיננסיים",
        "⚖️ השוואה ענפית",
        "🌩️ Stress Test (מבחני קיצון)"
    ])

    with tabs[0]:
        st.subheader("פילוח מרווח שירות חוזי (CSM) ומודל מדידה")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(names=['ביטוח חיים', 'ביטוח בריאות', 'ביטוח כללי'], 
                                   values=[d['life_csm'], d['health_csm'], d['general_csm']], 
                                   title="התפלגות CSM לפי מגזרי פעילות", hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(names=['גישת העמלה המשתנה (VFA)', 'מודל המדידה הכללי (GMM)'], 
                                   values=[d['vfa_csm_pct'], 100-d['vfa_csm_pct']], 
                                   title="מתודולוגיית מדידת התחייבויות ביטוחיות", hole=0.5,
                                   color_discrete_sequence=['#FFD700', '#87CEEB']), use_container_width=True)

    with tabs[1]:
        st.subheader("פילוח נכסים מנוהלים (AUM) וחשיפת נוסטרו")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            aum_data = pd.DataFrame({
                'קטגוריה': ['קרנות פנסיה', 'קופות גמל', 'חוזי השקעה', 'נכסי VFA'],
                'מיליארדי ש"ח': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]
            })
            st.plotly_chart(px.bar(aum_data, x='קטגוריה', y='מיליארדי ש"ח', color='קטגוריה', text='מיליארדי ש"ח',
                                   title="נכסים מנוהלים לפי סוג פעילות"), use_container_width=True)
        with col_b:
            assets = pd.DataFrame({'נכס': ['נדל"ן', 'מניות', 'אלטרנטיבי'], 
                                   'חשיפה (%)': [d['re_pct'], d['equity_pct'], d['alts_pct']]})
            st.plotly_chart(px.pie(assets, names='נכס', values='חשיפה (%)', hole=0.3, title="חשיפת נוסטרו לנכסי סיכון"), use_container_width=True)

    with tabs[2]:
        st.subheader("ניתוח יחסים פיננסיים (מאזן, רווח ו-IFRS 17)")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.write("**📊 יחסי IFRS 17**")
            st.metric("שיעור שחרור CSM", f"{d['csm_release_rate']}%")
            st.metric("מרווח עסקים חדשים", f"{d['new_biz_margin']}%")
            st.metric("יחס CSM להון עצמי", f"{d['csm_to_equity']}")
        with r2:
            st.write("**💰 יחסי מאזן ותפעול**")
            st.metric("הון עצמי לסך מאזן", f"{d['equity_to_assets']}%")
            st.metric("יחס הוצאות הנהלה", f"{d['expense_ratio']}%")
            st.metric("יחס תביעות (Claims)", f"{d['claims_ratio']}%")
        with r3:
            st.write("**💸 יחסי תזרים וחוסן**")
            st.metric("יחס תזרים מפעילות", f"{d['op_cash_flow_ratio']}")
            st.metric("יחס הון רובד 1", f"{d['tier1_ratio']}%")
            st.metric("מדד נזילות שוטפת", f"{d['liquidity']}")

    with tabs[3]:
        st.subheader("מיקום החברה אל מול השוק")
        st.plotly_chart(px.scatter(df, x="solvency_ratio", y="roe", size="csm_total", color="company", text="company",
                                   labels={"solvency_ratio": "יחס כושר פירעון (%)", "roe": "ROE (%)"}), use_container_width=True)

    with tabs[4]:
        st.subheader("🌩️ Stress Test: מבחני רגישות משולבים")
        s1, s2, s3 = st.columns(3)
        m_s = s1.slider("זעזוע שוק המניות (%)", 0, 40, 0)
        i_s = s2.slider("שינוי בעקום הריבית (BPS)", -100, 100, 0)
        l_s = s3.slider("עלייה בשיעור ביטולים (Lapse) %", 0, 20, 0)
        
        impact = (m_s * d['mkt_sens']) + (abs(i_s/100) * d['int_sens']) + (l_s * d['lapse_sens'])
        new_sol = max(0, d['solvency_ratio'] - impact)
        
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_sol, 
                                               title={'text': "יחס כושר פירעון חזוי"},
                                               gauge={'axis': {'range': [0, 250]},
                                                      'steps': [{'range': [0, 110], 'color': "red"}, 
                                                                {'range': [110, 150], 'color': "orange"}, 
                                                                {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
        if l_s > 0:
            st.warning(f"תרחיש הביטולים גרע {round(l_s * d['lapse_sens'], 2)}% מיחס ההון.")
else:
    st.error("נא לוודא שקובץ database.csv הועלה בצורה תקינה לתיקיית data.")
