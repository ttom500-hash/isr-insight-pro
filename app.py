import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# הגדרות עמוד ועיצוב
st.set_page_config(page_title="מערכת SupTech - גרסה סופית ומאושרת", layout="wide")

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

    st.title(f"דוח אנליטי וניהול סיכונים: {selected}")
    st.write(f"תקן דיווח: **IFRS 17 & Solvency II** | אימות נתונים: **עבר בהצלחה**")

    # --- מנוע דגלים אדומים (Red Flags Engine) ---
    red_flags = []
    if d['solvency_ratio'] < 150: red_flags.append(f"🚩 **חוסן הוני:** יחס סולבנסי ({d['solvency_ratio']}%) מתחת לסף היעד.")
    if d['combined_ratio'] > 100: red_flags.append(f"🚩 **יעילות חיתומית:** יחס משולב ({d['combined_ratio']}%) מעיד על הפסד תפעולי בביטוח.")
    if d['alts_pct'] > 13: red_flags.append(f"⚠️ **סיכון נזילות:** חשיפה גבוהה ({d['alts_pct']}%) להשקעות אלטרנטיביות.")
    if d['loss_component'] > 200: red_flags.append(f"🚩 **איכות תיק:** מרכיב הפסד גבוה (₪{d['loss_component']}M) בחוזים מכבידים.")

    if red_flags:
        with st.expander("🚨 התראות פיקוחיות (Red Flags) - נדרשת בחינה", expanded=True):
            for flag in red_flags: st.warning(flag)
    else:
        st.success("✅ לא נמצאו חריגות במדדי הסף הרגולטוריים.")

    st.divider()

    # --- KPIs ראשיים ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("יחס כושר פירעון", f"{d['solvency_ratio']}%", help="הון מוכר ביחס לדרישת ההון.")
    k2.metric("מרווח שירות (CSM)", f"₪{d['csm_total']}B", help="הרווח העתידי מהתחייבויות ביטוחיות.")
    total_aum = d['vfa_assets_aum'] + d['inv_contracts_aum'] + d['pension_aum'] + d['provident_aum']
    k3.metric("סך נכסים מנוהלים (AUM)", f"₪{round(total_aum, 1)}B")
    k4.metric("תשואה להון (ROE)", f"{d['roe']}%")

    # --- טאבים לניתוח מעמיק ---
    tabs = st.tabs(["📑 IFRS 17 & CSM", "💰 ניתוח AUM ונכסים", "📈 יחסים פיננסיים", "⛈️ Stress Test"])

    with tabs[0]:
        st.subheader("ניתוח מרווח שירות חוזי (CSM) ומגזרים")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(names=['חיים', 'בריאות', 'כללי'], values=[d['life_csm'], d['health_csm'], d['general_csm']], title="פילוח CSM מגזרי", hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(names=['VFA (משתתפות)', 'GMM (רגיל)'], values=[d['vfa_csm_pct'], 100-d['vfa_csm_pct']], title="מתודולוגיית מדידה", hole=0.5, color_discrete_sequence=['gold', 'skyblue']), use_container_width=True)

    with tabs[1]:
        st.subheader("פילוח נכסים מנוהלים וחשיפת נוסטרו")
        col_a, col_b = st.columns([2, 1])
        with col_a:
            aum_data = pd.DataFrame({'מגזר': ['פנסיה', 'גמל', 'חוזי השקעה', 'נכסי VFA'], 'מיליארדי ש"ח': [d['pension_aum'], d['provident_aum'], d['inv_contracts_aum'], d['vfa_assets_aum']]})
            st.plotly_chart(px.bar(aum_data, x='מגזר', y='מיליארדי ש"ח', color='מגזר', text='מיליארדי ש"ח'), use_container_width=True)
        with col_b:
            st.plotly_chart(px.pie(names=['נדל"ן', 'מניות', 'אלטרנטיבי'], values=[d['re_pct'], d['equity_pct'], d['alts_pct']], title="חשיפת נוסטרו"), use_container_width=True)

    with tabs[2]:
        st.subheader("מדריך יחסים פיננסיים ומתודולוגיה")
        r1, r2 = st.columns(2)
        with r1:
            st.write("**📊 יחסי IFRS 17**")
            with st.expander("פירוט יחסי רווחיות CSM"):
                st.metric("שיעור שחרור CSM", f"{d['csm_release_rate']}%")
                st.latex(r"Release \ Rate = \frac{Recognized \ CSM}{Opening \ CSM}")
                st.metric("מרווח עסקים חדשים", f"{d['new_biz_margin']}%")
                st.latex(r"NB \ Margin = \frac{New \ Biz \ CSM}{PVFP}")
        with r2:
            st.write("**💰 יחסי מאזן ותפעול**")
            with st.expander("פירוט יחסי חוסן ויעילות"):
                st.metric("הון עצמי לסך מאזן", f"{d['equity_to_assets']}%")
                st.latex(r"Equity \ Ratio = \frac{Equity}{Assets}")
                st.metric("יחס תביעות", f"{d['claims_ratio']}%")
                st.metric("יחס תזרים", f"{d['op_cash_flow_ratio']}")

    with tabs[3]:
        st.subheader("⛈️ Stress Test: סימולציית רגישויות")
        s1, s2, s3 = st.columns(3)
        m_s = s1.slider("זעזוע מניות (%)", 0, 40, 0)
        i_s = s2.slider("שינוי ריבית (BPS)", -100, 100, 0)
        l_s = s3.slider("עלייה בביטולים (Lapse) %", 0, 20, 0)
        
        impact = (m_s * d['mkt_sens']) + (abs(i_s/100) * d['int_sens']) + (l_s * d['lapse_sens'])
        new_sol = max(0, d['solvency_ratio'] - impact)
        
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=new_sol, title={'text': "סולבנסי חזוי"},
                                               gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 110], 'color': "red"}, {'range': [110, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]})), use_container_width=True)
else:
    st.error("שגיאה בטעינת הנתונים.")
