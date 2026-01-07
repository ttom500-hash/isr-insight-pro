import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# הגדרות עמוד לקריאות מקסימלית (High Contrast)
st.set_page_config(page_title="Insurance Supervision System", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 20px; border-radius: 12px; border: 1px solid #dee2e6; }
    .stMetric label { color: #1a3a5a !important; font-weight: bold !important; font-size: 18px !important; }
    .stMetric div { color: #212529 !important; }
    h1, h2, h3 { color: #1a3a5a; border-bottom: 2px solid #e9ecef; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    row = df[df['company'] == selected_company].iloc[-1]

    st.title(f"🏛️ מערכת פיקוח וניהול סיכונים: {selected_company}")
    st.info(f"תקופת דיווח: {row['quarter']} {row['year']} | מקור: {row['data_source']}")

    # יצירת טאבים להפרדה מקצועית
    tab1, tab2, tab3, tab4 = st.tabs(["📊 יציבות ו-KPIs", "📈 IFRS 17 מגזרי", "🧪 תרחישי קיצון", "⚖️ דוחות כספיים"])

    # --- טאב 1: מדדי יציבות ו-KPIs ---
    with tab1:
        st.subheader("5 מדדי הליבה הקריטיים [cite: 2026-01-03]")
        k1, k2, k3, k4, k5 = st.columns(5)
        
        with k1:
            st.metric("סולבנסי", f"{row['solvency_ratio']}%")
            with st.expander("ℹ️ הסבר פיקוחי"):
                st.write("**משמעות:** הלימות ההון של החברה מול סיכוניה.")
                st.info("💡 **הנחיה:** ודא שהיחס מעל 150%. מתחת ל-100% נדרשת עצירת דיבידנד.")
        
        with k2:
            st.metric("יתרת CSM", f"₪{row['csm_balance']}B")
            with st.expander("ℹ️ הסבר פיקוחי"):
                st.write("**משמעות:** רווח עתידי גלום בחוזים קיימים.")
                st.info("💡 **הנחיה:** גידול במדד מעיד על צבר רווחיות חזק לעתיד.")

        with k3:
            st.metric("מרכיב הפסד", f"₪{row['loss_component']}M")
            with st.expander("ℹ️ הסבר פיקוחי"):
                st.write("**משמעות:** התחייבויות בגין חוזי ביטוח הפסדיים.")
                st.warning("💡 **הנחיה:** עלייה חדה מעידה על כשל בתמחור הפוליסות.")

        with k4:
            st.metric("ROE (תשואה להון)", f"{row['roe']}%")
            with st.expander("ℹ️ הסבר פיקוחי"):
                st.write("**משמעות:** יעילות החברה ביצירת רווח לבעלי המניות.")
                st.info("💡 **הנחיה:** השווה למתחרים כדי לזהות חולשה ניהולית.")

        with k5:
            st.metric("נזילות", f"{row['liquidity']}x")
            with st.expander("ℹ️ הסבר פיקוחי"):
                st.write("**משמעות:** יכולת כיסוי התחייבויות מיידיות.")
                st.info("💡 **הנחיה:** ודא יחס מעל 1.0 לשמירה על יציבות תזרימית.")

    # --- טאב 2: IFRS 17 מגזרי ---
    with tab2:
        st.subheader("ניתוח IFRS 17 עמוק לפי מגזרי פעילות")
        
        # טבלה מגזרית
        seg_data = pd.DataFrame({
            "מדד פיננסי": ["קצב שחרור רווח (Release Rate)", "עצימות הון חדש (New Biz Strain)"],
            "חיים וחיסכון": [f"{row['life_release_rate']}%", f"{row['life_new_biz_strain']}%"],
            "בריאות": [f"{row['health_release_rate']}%", f"{row['health_new_biz_strain']}%"],
            "ביטוח כללי": [f"{row['general_release_rate']}%", f"{row['general_new_biz_strain']}%"]
        })
        st.table(seg_data)

        # הסברים מגזריים
        exp1, exp2 = st.columns(2)
        with exp1:
            st.markdown("**1. Release Rate (מגזרי):**")
            st.caption("קצב הפיכת ה-CSM לרווח חשבונאי.")
            st.info("💡 **למפקח:** קצב מהיר מדי בביטוח חיים עלול להחליש את עתודות העתיד.")
        with exp2:
            st.markdown("**2. New Business Strain (מגזרי):**")
            st.caption("ההון הנדרש לצורך רכישת פוליסות חדשות.")
            st.warning("💡 **למפקח:** Strain גבוה במגזר הכללי מעיד על תחרות מחירים מסוכנת.")

        st.divider()
        col_pie, col_ratio = st.columns(2)
        with col_pie:
            fig = px.pie(values=[row['life_csm'], row['health_csm'], row['general_csm']], 
                         names=["חיים", "בריאות", "כללי"], title="התפלגות CSM (שווי הוגן)")
            st.plotly_chart(fig)
        with col_ratio:
            st.metric("CSM to Equity Ratio", f"{row['csm_to_equity']}x")
            with st.expander("ℹ️ הסבר יחס"):
                st.write("מראה כמה רווח עתידי (CSM) יש לחברה על כל שקל של הון עצמי.")
                st.success("יחס מעל 1.0 מעיד על 'כרית' רווחית גדולה מאוד.")

    # --- טאב 3: תרחישי קיצון ---
    with tab3:
        st.subheader("🧪 סימולטור תרחישי קיצון (Stress Test)")
        c_sim1, c_sim2 = st.columns([1, 2])
        with c_sim1:
            st.write("**הגדר תרחיש שוק:**")
            s_int = st.select_slider("שינוי ריבית (bps)", options=[-100, -50, 0, 50, 100], value=0)
            s_mkt = st.slider("קריסת מניות (%)", -30, 0, 0)
            
            impact = (s_int/100 * row['int_sens'] * 100) + (s_mkt/10 * row['mkt_sens'] * 100)
            res_solv = row['solvency_ratio'] + impact
            st.metric("סולבנסי בתרחיש", f"{res_solv:.1f}%", delta=f"{impact:.1f}%")
            
        with c_sim2:
            fig_g = go.Figure(go.Indicator(mode="gauge+number", value=res_solv,
                gauge={'axis': {'range': [0, 250]}, 
                       'steps': [{'range': [0, 100], 'color': "#ff4b4b"}, 
                                 {'range': [100, 150], 'color': "#ffa500"}, 
                                 {'range': [150, 250], 'color': "#00cc96"}]}))
            st.plotly_chart(fig_g)

    # --- טאב 4: דוחות כספיים משלימים ---
    with tab4:
        st.subheader("ניתוח דוחות כספיים הוליסטי")
        cp, cb, cf = st.columns(3)
        
        with cp:
            st.markdown("### דוח רווח והפסד")
            st.metric("יחס משולב", f"{row['combined_ratio']}%")
            st.metric("יחס הוצאות הנהלה", f"{row['expense_ratio']}%")
            with st.expander("ℹ️ הסבר"):
                st.write("יחס משולב מעל 100% מעיד על הפסד חיתומי (תביעות > פרמיות).")

        with cb:
            st.markdown("### מאזן וחוסן")
            st.metric("הון למאזן", f"{row['equity_to_balance']}%")
            st.metric("Tier 1 Capital Ratio", f"{row['tier1_ratio']}%")
            with st.expander("ℹ️ הסבר"):
                st.write("Tier 1 מייצג את ההון האיכותי ביותר הזמין לספיגת הפסדים.")

        with cf:
            st.markdown("### תזרים מזומנים")
            st.metric("תזרים מפעילות", f"₪{row['operating_cash_flow']}B")
            with st.expander("ℹ️ הסבר"):
                st.write("תזרים מפעילות שוטפת מאשר שהרווח הדיווח מתורגם למזומן.")

except Exception as e:
    st.error(f"שגיאה בטעינה: {e}")
