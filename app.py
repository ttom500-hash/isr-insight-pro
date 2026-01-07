import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות תצוגה מקצועיות
st.set_page_config(page_title="מערכת SupTech - ניתוח פיננסי הוליסטי", layout="wide")

@st.cache_data
def load_data():
    path = 'data/database.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

df = load_data()

if not df.empty:
    st.sidebar.title("🔍 ניווט רגולטורי")
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    d = df[df['company'] == selected_company].iloc[-1]

    st.title(f"דוח פיקוחי מקיף: {selected_company} (נתוני 2025)")
    st.write(f"תקן דיווח: **IFRS 17 / Solvency II** | אימות מחסן נתונים: **V**")

    # --- מנוע דגלים אדומים (Red Flags Logic) ---
    red_flags = []
    if d['solvency_ratio'] < 150: red_flags.append(f"🚩 **חוסן הוני:** יחס סולבנסי ({d['solvency_ratio']}%) מתחת ליעד הרגולטורי.")
    if d['combined_ratio'] > 100: red_flags.append(f"🚩 **יעילות חיתומית:** הפסד במגזר הכללי (Combined: {d['combined_ratio']}%).")
    if d['alts_pct'] > 13: red_flags.append(f"⚠️ **סיכון נזילות:** חשיפה גבוהה ({d['alts_pct']}%) להשקעות אלטרנטיביות.")
    
    if red_flags:
        with st.expander("🚨 דגלים אדומים והתראות פיקוחיות", expanded=True):
            for f in red_flags: st.warning(f)
    else:
        st.success("✅ לא נמצאו חריגות מהותיות במדדי היציבות.")

    st.divider()

    # --- KPIs ראשיים (Top Level Overview) ---
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("יחס כושר פירעון", f"{d['solvency_ratio']}%", help="הון מוכר ביחס לדרישת SCR")
    k2.metric("יתרת CSM", f"₪{d['csm_total']}B", help="מרווח שירות חוזי (רווח עתידי)")
    total_aum = d['vfa_assets_aum'] + d['inv_contracts_aum'] + d['pension_aum'] + d['provident_aum']
    k3.metric("סך AUM מנוהל", f"₪{round(total_aum, 1)}B")
    k4.metric("ROE (תשואה להון)", f"{d['roe']}%")
    k5.metric("יחס משולב", f"{d['combined_ratio']}%", help="Combined Ratio למגזר הכללי")

    # --- טאבים הוליסטיים (Integrated Analysis) ---
    tabs = st.tabs(["📑 IFRS 17 ומגזרים", "💰 נכסים מנוהלים", "📈 יחסים פיננסיים", "⛈️ Stress Test"])

    with tabs[0]:
        st.subheader("ניתוח מגזרי ומודלי מדידה")
        
        c1, c2 = st.columns(2)
        with c1:
            # פילוח CSM מגזרי
            csm_df = pd.DataFrame({
                'Sector': ['חיים', 'בריאות', 'כללי'],
                'Value': [d['life_csm'], d['health_csm'], d['general_csm']]
            })
            st.plotly_chart(px.pie(csm_df, names='Sector', values='Value', title="התפלגות CSM/PAA לפי מגזר", hole=0.4), use_container_width=True)
        with c2:
            # מודלים חשבונאיים
            models_df = pd.DataFrame({
                'Model': ['VFA (משתתפות)', 'PAA (מפושט)', 'GMM (כללי)'],
                'Share': [d['vfa_csm_pct'], d['paa_pct'], 100 - (d['vfa_csm_pct'] + d['paa_pct'])]
            })
            st.plotly_chart(px.pie(models_df, names='Model', values='Share', title="תמהיל מודלים בתיק", hole=0.5), use_container_width=True)

    with tabs[1]:
        st.subheader("הפרדת נכסים מנוהלים (AUM) וחשיפת נוסטרו")
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            aum_df = pd.DataFrame({
                'Type': ['פנסיה', 'גמל', 'חוזי השקעה', 'נכסי VFA'],
                'Amount': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]
            })
            st.plotly_chart(px.bar(aum_df, x='Type', y='Amount', color='Type', text='Amount', title='נכסים מנוהלים במיליארדי ש"ח'), use_container_width=True)
        with col_b:
            # חשיפת נוסטרו
            nostro_df = pd.DataFrame({
                'Asset': ['נדל"ן', 'מניות', 'אלטרנטיבי'],
                'Pct': [d['re_pct'], d['equity_pct'], d['alts_pct']]
            })
            st.plotly_chart(px.pie(nostro_df, names='Asset', values='Pct', title="חשיפת נוסטרו לנכסי סיכון", hole=0.3), use_container_width=True)

    with tabs[2]:
        st.subheader("מרכז ידע ויחסים פיננסיים")
        r1, r2 = st.columns(2)
        with r1:
            st.write("**📑 יחסי IFRS 17**")
            with st.expander("הסבר ונוסחאות"):
                st.metric("שיעור שחרור CSM", f"{d['csm_release_rate']}%")
                st.latex(r"Release \ Rate = \frac{Recognized \ CSM}{Opening \ CSM}")
                st.metric("מרווח עסקים חדשים", f"{d['new_biz_margin']}%")
        with r2:
            st.write("**💰 יחסי מאזן ותפעול**")
            with st.expander("הסבר ונוסחאות"):
                st.metric("הון עצמי לנכסים", f"{d['equity_to_assets']}%")
                st.metric("יחס הוצאות הנהלה", f"{d['expense_ratio']}%")
                st.metric("יחס תזרים מפעילות", f"{d['op_cash_flow_ratio']}")

    with tabs[3]:
        st.subheader("⛈️ Stress Test: סימולטור רגישויות")
        
        s1, s2, s3 = st.columns(3)
        m_s = s1.slider("זעזוע מניות (%)", 0, 40, 0)
        i_s = s2.slider("שינוי ריבית (BPS)", -100, 100, 0)
        l_s = s3.slider("עלייה בביטולים (Lapse) %", 0, 20, 0)
        
        impact = (m_s * d['mkt_sens']) + (abs(i_s/100) * d['int_sens']) + (l_s * d['lapse_sens'])
        new_sol = max(0, d['solvency_ratio'] - impact)
        
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_sol, title={'text': "סולבנסי חזוי"},
                                               gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 110], 'color': "red"}, {'range': [110, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
else:
    st.error("שגיאה בטעינת נתוני 2025.")
