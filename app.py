import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות מערכת
st.set_page_config(page_title="מערכת פיקוח SupTech - גרסה סופית", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

df = load_data()

if not df.empty:
    # --- תפריט צד ---
    st.sidebar.title("🔍 ניתוח רגולטורי מקיף")
    selected_company = st.sidebar.selectbox("בחר חברה לסקירה:", df['company'].unique())
    d = df[df['company'] == selected_company].iloc[-1]

    # --- כותרת ונתוני על ---
    st.title(f"דוח פיקוח וניתוח סיכונים: {selected_company}")
    st.write(f"נתונים מעודכנים לרבעון 3, 2025 | תקן דיווח: **IFRS 17 & Solvency II**")
    
    # --- KPIs ראשיים ---
    st.divider()
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("יחס כושר פירעון", f"{d['solvency_ratio']}%")
    k2.metric("מרווח שירות (CSM)", f"₪{d['csm_total']}B")
    k3.metric("תשואה להון (ROE)", f"{d['roe']}%")
    k4.metric("חוזי השקעה (AUM)", f"₪{d['inv_contracts_aum']}B")
    k5.metric("יחס הון רובד 1", f"{d['tier1_ratio']}%")

    # --- טאבים לניתוח מעמיק ---
    t1, t2, t3, t4 = st.tabs(["📋 ניתוח מגזרים (Segments)", "🏗️ תיק השקעות ונוסטרו", "⚖️ השוואה ענפית", "⛈️ מבחני קיצון"])

    with t1:
        st.subheader("פילוח רווחיות ומרווח שירות (CSM) לפי מגזרי פעילות")
        col1, col2 = st.columns(2)
        with col1:
            # פילוח CSM
            fig_pie = px.pie(names=['ביטוח חיים', 'ביטוח בריאות', 'ביטוח כללי'], 
                             values=[d['life_csm'], d['health_csm'], d['general_csm']], 
                             title="התפלגות מרווח שירות חוזי (CSM)", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            # השוואת רווחיות (ROE) מגזרית
            seg_roe = pd.DataFrame({
                'מגזר': ['חיים', 'בריאות', 'כללי'],
                'ROE (%)': [d['life_roe'], d['health_roe'], d['general_roe']]
            })
            st.plotly_chart(px.bar(seg_roe, x='מגזר', y='ROE (%)', color='מגזר', title="רווחיות (ROE) לפי מגזר פעילות"), use_container_width=True)
        
        st.info(f"שיעור פוליסות משתתפות (VFA) בתיק: {d['vfa_pct']}%")

    with t2:
        st.subheader("ניתוח נכסים המגבים התחייבויות (Asset Allocation)")
        c_a, c_b = st.columns([2, 1])
        with c_a:
            assets = pd.DataFrame({
                'סוג נכס': ['נדל"ן להשקעה', 'ניירות ערך הוניים', 'השקעות אלטרנטיביות', 'אג"ח ומזומן'],
                'שיעור (%)': [d['re_pct'], d['equity_pct'], d['alts_pct'], 100-(d['re_pct']+d['equity_pct']+d['alts_pct'])]
            })
            st.plotly_chart(px.bar(assets, x='סוג נכס', y='שיעור (%)', color='סוג נכס', text='שיעור (%)'), use_container_width=True)
        with c_b:
            st.write("**פירוט חשיפות:**")
            st.write(f"- נדל''ן להשקעה: {d['re_pct']}%")
            st.write(f"- מניות (Equities): {d['equity_pct']}%")
            st.write(f"- אלטרנטיבי (Alts): {d['alts_pct']}%")
            st.warning("חשיפה גבוהה לנכסים אלטרנטיביים דורשת בחינת נזילות תקופתית.")

    with t3:
        st.subheader("מיקום החברה במפת הסיכון הענפית")
        fig_scatter = px.scatter(df, x="solvency_ratio", y="roe", size="csm_total", color="company", text="company",
                                 labels={"solvency_ratio": "יחס כושר פירעון (%)", "roe": "תשואה להון (%)"},
                                 title="חוסן הוני מול רווחיות (גודל הבועה = יתרת CSM)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with t4:
        st.subheader("⛈️ Stress Test: מבחני רגישות הון")
        st.write("נוסחת השפעת זעזועים על יחס כושר הפירעון:")
        st.latex(r"Solvency_{New} = Solvency_{Old} - \sum (Shock_i \times Sensitivity_i)")
        
        s1, s2, s3 = st.columns(3)
        m_shock = s1.slider("זעזוע שוק המניות (%)", 0, 40, 0)
        i_shock = s2.slider("שינוי ריבית (BPS)", -100, 100, 0)
        l_shock = s3.slider("עלייה בביטולים (%)", 0, 20, 0)
        
        # חישוב השפעה
        total_impact = (m_shock * d['mkt_sens']) + (abs(i_shock/100) * d['int_sens']) + (l_shock * d['lapse_sens'])
        final_sol = max(0, d['solvency_ratio'] - total_impact)
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = final_sol,
            gauge = {'axis': {'range': [0, 250]},
                     'steps': [
                         {'range': [0, 110], 'color': "red"},
                         {'range': [110, 150], 'color': "orange"},
                         {'range': [150, 250], 'color': "green"}]},
            title = {'text': "יחס כושר פירעון חזוי"}))
        st.plotly_chart(fig_gauge, use_container_width=True)

else:
    st.error("קובץ הנתונים ריק או חסר. נא לעדכן את database.csv")
