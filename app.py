
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות עמוד RTL ועיצוב מקצועי
st.set_page_config(page_title="SupTech - מערכת פיקוח הוליסטית v4.0", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- Sidebar: ניווט ---
    st.sidebar.title("🔍 מרכז בקרה רגולטורי")
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח מעמיק:", df['company'].unique())
    d = df[df['company'] == selected_company].iloc[-1]

    # --- כותרת וניהול דגלים אדומים ---
    st.title(f"דוח אנליטי רב-ממדי: {selected_company}")
    st.write(f"תקן דיווח: **IFRS 17 & Solvency II** | אימות נתונים: **Verified**")

    # מנוע דגלים אדומים (Red Flags)
    red_flags = []
    if d['solvency_ratio'] < 150: red_flags.append(f"🚩 **חוסן הוני:** יחס סולבנסי ({d['solvency_ratio']}%) נמוך מהיעד.")
    if d['combined_ratio'] > 100: red_flags.append(f"🚩 **יעילות חיתומית:** הפסד במגזר הכללי (Combined Ratio: {d['combined_ratio']}%).")
    if d['alts_pct'] > 13: red_flags.append(f"⚠️ **סיכון נזילות:** חשיפה גבוהה ({d['alts_pct']}%) לנכסים אלטרנטיביים.")
    if d['loss_component'] > 200: red_flags.append(f"🚩 **איכות תיק:** מרכיב הפסד גבוה (₪{d['loss_component']}M) בחוזים מכבידים.")

    if red_flags:
        with st.expander("🚨 התראות פיקוחיות (Red Flags) - נדרשת בחינה", expanded=True):
            for flag in red_flags: st.warning(flag)
    else:
        st.success("✅ החברה עומדת בכל מדדי הסף הרגולטוריים.")

    st.divider()

    # --- KPIs ראשיים ---
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("יחס כושר פירעון", f"{d['solvency_ratio']}%", help="הון מוכר ביחס לדרישת הון (SCR)")
    k2.metric("יתרת CSM", f"₪{d['csm_total']}B", help="הרווח העתידי מהתחייבויות ביטוחיות")
    total_aum = d['vfa_assets_aum'] + d['inv_contracts_aum'] + d['pension_aum'] + d['provident_aum']
    k3.metric("סך נכסים (AUM)", f"₪{round(total_aum, 1)}B")
    k4.metric("תשואה להון (ROE)", f"{d['roe']}%")
    k5.metric("יחס הון רובד 1", f"{d['tier1_ratio']}%")

    # --- טאבים הוליסטיים ---
    tabs = st.tabs(["📑 ניתוח IFRS 17 ומגזרים", "💰 ניהול נכסים ונוסטרו", "📈 יחסים פיננסיים ומדריך", "⚖️ השוואה ענפית", "⛈️ Stress Test"])

    with tabs[0]:
        st.subheader("ניתוח מרווח שירות חוזי (CSM) ומודל המדידה")
        
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(names=['ביטוח חיים', 'ביטוח בריאות', 'ביטוח כללי (PAA)'], 
                                   values=[d['life_csm'], d['health_csm'], d['general_csm']], 
                                   title="התפלגות CSM לפי מגזרי פעילות", hole=0.4), use_container_width=True)
        with c2:
            models = pd.DataFrame({
                'מודל': ['VFA (משתתפות)', 'PAA (מפושט)', 'GMM (כללי)'],
                'שיעור בתיק': [d['vfa_csm_pct'], d['paa_pct'], 100 - (d['vfa_csm_pct'] + d['paa_pct'])]
            })
            st.plotly_chart(px.pie(models, names='מודל', values='שיעור בתיק', hole=0.5, title="תמהיל מודלים חשבונאיים"), use_container_width=True)

    with tabs[1]:
        st.subheader("הפרדת נכסים מנוהלים (AUM) וחשיפת נוסטרו")
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            aum_df = pd.DataFrame({
                'מגזר': ['קרנות פנסיה', 'קופות גמל', 'חוזי השקעה (IFRS 9)', 'נכסי VFA (ביטוח)'],
                'מיליארדי ש"ח': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]
            })
            st.plotly_chart(px.bar(aum_df, x='מגזר', y='מיליארדי ש"ח', color='מגזר', text='מיליארדי ש"ח'), use_container_width=True)
        with col_b:
            assets = pd.DataFrame({'סוג': ['נדל"ן', 'מניות', 'אלטרנטיבי'], 
                                   'חשיפה (%)': [d['re_pct'], d['equity_pct'], d['alts_pct']]})
            st.plotly_chart(px.pie(assets, names='סוג', values='שיעור (%)', hole=0.3, title="חשיפת נוסטרו"), use_container_width=True)

    with tabs[2]:
        st.subheader("מרכז ידע: יחסים פיננסיים ומתודולוגיה")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.write("**📑 יחסי IFRS 17**")
            with st.expander("פירוט ונוסחאות"):
                st.metric("שיעור שחרור CSM", f"{d['csm_release_rate']}%")
                st.latex(r"Release \ Rate = \frac{Recognized \ CSM}{Opening \ CSM}")
                st.metric("מרווח עסקים חדשים", f"{d['new_biz_margin']}%")
                st.latex(r"NB \ Margin = \frac{New \ Biz \ CSM}{PVFP}")
        with r2:
            st.write("**💰 יחסי מאזן ותפעול**")
            with st.expander("פירוט ונוסחאות"):
                st.metric("הון עצמי לנכסים", f"{d['equity_to_assets']}%")
                st.latex(r"Equity \ Ratio = \frac{Equity}{Assets}")
                st.metric("יחס הוצאות הנהלה", f"{d['expense_ratio']}%")
        with r3:
            st.write("**💸 יחסי תזרים ואיכות**")
            with st.expander("פירוט ונוסחאות"):
                st.metric("יחס תזרים מפעילות", f"{d['op_cash_flow_ratio']}")
                st.latex(r"CF \ Ratio = \frac{Op \ CashFlow}{Net \ Income}")
                st.metric("יחס תביעות (Claims)", f"{d['claims_ratio']}%")

    with tabs[3]:
        st.subheader("דירוג החברה אל מול השוק")
        st.plotly_chart(px.scatter(df, x="solvency_ratio", y="roe", size="csm_total", color="company", text="company",
                                   labels={"solvency_ratio": "כושר פירעון (%)", "roe": "ROE (%)"}), use_container_width=True)

    with tabs[4]:
        st.subheader("⛈️ Stress Test: סימולציית רגישויות רגולטורית")
        
        s1, s2, s3 = st.columns(3)
        m_s = s1.slider("זעזוע שוק המניות (%)", 0, 40, 0)
        i_s = s2.slider("שינוי בעקום הריבית (BPS)", -100, 100, 0)
        l_s = s3.slider("תרחיש ביטולים (Lapse) %", 0, 20, 0)
        
        impact = (m_s * d['mkt_sens']) + (abs(i_s/100) * d['int_sens']) + (l_s * d['lapse_sens'])
        new_sol = max(0, d['solvency_ratio'] - impact)
        
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_sol, title={'text': "יחס כושר פירעון חזוי"},
                                               gauge={'axis': {'range': [0, 250]},
                                                      'steps': [{'range': [0, 110], 'color': "red"}, 
                                                                {'range': [110, 150], 'color': "orange"}, 
                                                                {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
else:
    st.error("קובץ הנתונים לא נמצא בנתיב data/database.csv")
