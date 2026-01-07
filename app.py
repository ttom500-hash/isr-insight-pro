import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="SupTech Insurance Analytics - Full IFRS 17 Suite", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

df = load_data()

if not df.empty:
    st.sidebar.title("🔍 ניתוח רגולטורי מקיף")
    selected = st.sidebar.selectbox("בחר חברה:", df['company'].unique())
    d = df[df['company'] == selected].iloc[-1]

    st.title(f"דוח אנליטי: {selected} - IFRS 17 Deep Dive")
    
    # --- דגלים אדומים בראש הדף ---
    red_flags = []
    if d['solvency_ratio'] < 150: red_flags.append(f"🚩 סולבנסי נמוך: {d['solvency_ratio']}%")
    if d['combined_ratio'] > 100: red_flags.append(f"🚩 הפסד חיתומי (PAA): {d['combined_ratio']}%")
    if red_flags:
        with st.expander("🚨 התראות רגולטוריות", expanded=True):
            for f in red_flags: st.warning(f)

    st.divider()

    # KPIs ראשיים
    cols = st.columns(5)
    cols[0].metric("כושר פירעון", f"{d['solvency_ratio']}%")
    cols[1].metric("יתרת CSM", f"₪{d['csm_total']}B")
    cols[2].metric("מרווח PAA", f"{d['paa_margin']}%")
    cols[3].metric("ROE", f"{d['roe']}%")
    cols[4].metric("AUM כולל", f"₪{round(d['vfa_assets_aum'] + d['inv_contracts_aum'] + d['pension_aum'] + d['provident_aum'], 1)}B")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📑 מודלים IFRS 17 (GMM/VFA/PAA)", 
        "🏘️ ניתוח CSM מגזרי", 
        "📈 יחסי רווחיות ויעילות",
        "💰 נכסים מנוהלים",
        "⛈️ Stress Test"
    ])

    with tab1:
        st.subheader("התפלגות מודלי מדידה (Measurement Models)")
        with st.expander("💡 הסבר על המודלים"):
            st.write("**VFA:** מיושם על פוליסות משתתפות. **PAA:** מודל מפושט לחוזים קצרי טווח (אלמנטרי). **GMM:** המודל הכללי לביטוח חיים מסורתי.")
        
        c1, c2 = st.columns(2)
        with c1:
            models = pd.DataFrame({
                'מודל': ['VFA (משתתפות)', 'PAA (מפושט)', 'GMM (כללי)'],
                'שיעור בתיק': [d['vfa_csm_pct'], d['paa_pct'], 100 - (d['vfa_csm_pct'] + d['paa_pct'])]
            })
            st.plotly_chart(px.pie(models, names='מודל', values='שיעור בתיק', hole=0.5, title="תמהיל מודלים חשבונאיים"), use_container_width=True)
        with c2:
            st.metric("יחס משולב (Combined Ratio)", f"{d['combined_ratio']}%")
            st.caption("מדד מרכזי לרווחיות מודל ה-PAA (ביטוח כללי).")
            st.latex(r"Combined \ Ratio = \frac{Claims + Expenses}{Earned \ Premium}")

    with tab2:
        st.subheader("ניתוח CSM ומגזרי פעילות")
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(names=['חיים', 'בריאות', 'כללי'], values=[d['life_csm'], d['health_csm'], d['general_csm']], title="יתרת CSM/LRC לפי מגזר")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            growth = pd.DataFrame({
                'מגזר': ['חיים', 'בריאות'],
                'צמיחת CSM (%)': [d['life_csm_growth'], d['health_csm_growth']]
            })
            st.plotly_chart(px.bar(growth, x='מגזר', y='צמיחת CSM (%)', color='מגזר', title="צמיחת CSM אורגנית"), use_container_width=True)

    with tab3:
        st.subheader("יחסים פיננסיים מתקדמים")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.write("**יחסי IFRS 17**")
            st.metric("שיעור שחרור CSM", f"{d['csm_release_rate']}%")
            st.metric("מרווח עסקים חדשים", f"{d['new_biz_margin']}%")
        with r2:
            st.write("**יחסי תפעול**")
            st.metric("יחס הוצאות הנהלה", f"{d['expense_ratio']}%")
            st.metric("יחס תביעות", f"{d['claims_ratio']}%")
        with r3:
            st.write("**יחסי מאזן**")
            st.metric("הון עצמי לנכסים", f"{d['equity_to_assets']}%")
            st.metric("יחס CSM להון", f"{d['csm_to_equity']}")

    with tab4:
        st.subheader("ניהול נכסים (AUM)")
        aum_df = pd.DataFrame({
            'קטגוריה': ['פנסיה', 'גמל', 'חוזי השקעה', 'נכסי VFA'],
            '₪ מיליארד': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]
        })
        st.plotly_chart(px.bar(aum_df, x='קטגוריה', y='₪ מיליארד', color='קטגוריה'), use_container_width=True)

    with tab5:
        st.subheader("⛈️ Stress Test: סימולציית רגישויות")
        s1, s2, s3 = st.columns(3)
        m_shock = s1.slider("זעזוע מניות (%)", 0, 40, 0)
        i_shock = s2.slider("שינוי ריבית (BPS)", -100, 100, 0)
        l_shock = s3.slider("ביטולים (Lapse) %", 0, 20, 0)
        
        impact = (m_shock * d['mkt_sens']) + (abs(i_shock/100) * d['int_sens']) + (l_shock * d['lapse_sens'])
        new_sol = max(0, d['solvency_ratio'] - impact)
        
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_sol, title={'text': "סולבנסי חזוי"},
                                               gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 110], 'color': "red"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
else:
    st.error("קובץ הנתונים לא נמצא.")
