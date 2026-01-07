import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# הגדרות עמוד לקריאות מקסימלית
st.set_page_config(page_title="Insurance Supervision System", layout="wide")

# עיצוב נקי (High Contrast)
st.markdown("""
    <style>
    .reportview-container { background: #ffffff; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; color: #212529; }
    .stAlert { border-radius: 10px; }
    h1, h2, h3 { color: #1a3a5a; }
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

    # --- טאב 1: מדדי יציבות ו-KPIs ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 יציבות ו-KPIs", "📈 IFRS 17 מגזרי", "🧪 תרחישי קיצון", "⚖️ דוחות כספיים"])

    with tab1:
        st.subheader("5 מדדי הליבה הקריטיים [cite: 2026-01-03]")
        k1, k2, k3, k4, k5 = st.columns(5)
        
        with k1:
            st.metric("סולבנסי", f"{row['solvency_ratio']}%")
            with st.expander("ℹ️ הסבר"):
                st.write("**משמעות:** הלימות ההון של החברה מול סיכוניה.")
                st.info("💡 **פעולה:** ודא שהיחס מעל 150%. מתחת ל-100% נדרשת התערבות מיידית.")
        
        with k2:
            st.metric("יתרת CSM", f"₪{row['csm_balance']}B")
            with st.expander("ℹ️ הסבר"):
                st.write("**משמעות:** רווח עתידי שטרם הוכר מהסכמי ביטוח.")
                st.info("💡 **פעולה:** עקוב אחר מגמת הגידול - CSM צומח מעיד על עתיד רווחי.")

        with k3:
            st.metric("מרכיב הפסד", f"₪{row['loss_component']}M")
            with st.expander("ℹ️ הסבר"):
                st.write("**משמעות:** הפסדים מיידיים מחוזים מכבידים.")
                st.warning("💡 **פעולה:** עלייה במדד זה דורשת בחינה של תמחור הפוליסות.")

        with k4:
            st.metric("ROE", f"{row['roe']}%")
            with st.expander("ℹ️ הסבר"):
                st.write("**משמעות:** תשואה על ההון העצמי.")
                st.info("💡 **פעולה:** השווה לממוצע הענפי לבחינת יעילות ניהול ההון.")

        with k5:
            st.metric("נזילות", f"{row['liquidity']}x")
            with st.expander("ℹ️ הסבר"):
                st.write("**משמעות:** יכולת עמידה בהתחייבויות קצרות טווח.")
                st.info("💡 **פעולה:** ודא יחס מעל 1.0 לשמירה על נזילות תפעולית.")

    # --- טאב 2: IFRS 17 מגזרי ---
    with tab2:
        st.subheader("ניתוח IFRS 17 עמוק לפי מגזרי פעילות")
        
        # יצירת טבלה מגזרית מפורטת
        seg_data = pd.DataFrame({
            "מדד": ["CSM Release Rate", "New Business Strain"],
            "חיים וחיסכון": [f"{row['life_release_rate']}%", f"{row['life_new_biz_strain']}%"],
            "בריאות": [f"{row['health_release_rate']}%", f"{row['health_new_biz_strain']}%"],
            "ביטוח כללי": [f"{row['general_release_rate']}%", f"{row['general_new_biz_strain']}%"]
        })
        st.table(seg_data)

        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**1. קצב שחרור CSM (Release Rate):**")
            st.write("מראה כמה מהר הרווח העתידי הופך לרווח בדו\"ח.")
            st.info("💡 **למפקח:** קצב גבוה בביטוח כללי (מעל 12%) הוא תקין עקב קוצר הפוליסות. בחיים, קצב מעל 8% דורש בירור.")
        
        with col_b:
            st.write("**2. עצימות הון חדש (New Business Strain):**")
            st.write("ההון הנדרש לגיוס מכירות חדשות.")
            st.info("💡 **למפקח:** Strain גבוה מדי מעיד על צמיחה אגרסיבית שעלולה לסכן את עודפי ההון.")

        st.subheader("התפלגות CSM והון")
        c_pie1, c_pie2 = st.columns(2)
        with c_pie1:
            fig = px.pie(values=[row['life_csm'], row['health_csm'], row['general_csm']], names=["חיים", "בריאות", "כללי"], title="פיזור CSM מגזרי")
            st.plotly_chart(fig)
        with c_pie2:
            st.metric("CSM to Equity Ratio", f"{row['csm_to_equity']}x")
            st.write("**הסבר:** יחס הרווח הצבור להון הקיים. מעל 1.0 נחשב לחוסן גבוה מאוד.")

    # --- טאב 3: תרחישי קיצון ---
    with tab3:
        st.subheader("סימולטור רגישות סולבנסי")
        s_int = st.select_slider("תרחיש ריבית (bps)", options=[-100, -50, 0, 50, 100], value=0)
        s_mkt = st.slider("קריסת מניות (%)", -30, 0, 0)
        
        impact = (s_int/100 * row['int_sens'] * 100) + (s_mkt/10 * row['mkt_sens'] * 100)
        res_solv = row['solvency_ratio'] + impact
        
        st.metric("סולבנסי מותאם", f"{res_solv:.1f}%", delta=f"{impact:.1f}%")
        
        fig_g = go.Figure(go.Indicator(mode="gauge+number", value=res_solv, domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 100], 'color': "red"}, {'range': [100, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]}))
        st.plotly_chart(fig_g)

    # --- טאב 4: דוחות כספיים משלימים ---
    with tab4:
        st.subheader("ניתוח מאזן, רווח והפסד ותזרים")
        c_p, c_b, c_f = st.columns(3)
        
        with c_p:
            st.write("**רווח והפסד**")
            st.metric("יחס משולב", f"{row['combined_ratio']}%")
            st.metric("יחס הוצאות הנהלה", f"{row['expense_ratio']}%")
            st.caption("Combined Ratio מעל 100% מעיד על הפסד חיתומי.")

        with c_b:
            st.write("**מאזן**")
            st.metric("הון למאזן", f"{row['equity_to_balance']}%")
            st.metric("Tier 1 Ratio", f"{row['tier1_ratio']}%")
            st.caption("Tier 1 מייצג את ההון האיכותי ביותר של החברה.")

        with t_cf := c_f:
            st.write("**תזרים מזומנים**")
            st.metric("תזרים מפעילות", f"₪{row['operating_cash_flow']}B")
            st.caption("תזרים חיובי חיוני ליכולת חלוקת דיבידנד.")

except Exception as e:
    st.error(f"שגיאה: ודא שקובץ ה-CSV מעודכן עם כל העמודות החדשות. פירוט: {e}")
