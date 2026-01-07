import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# הגדרות תצוגה מקצועיות
st.set_page_config(page_title="Insurance Intelligence - Full Stack Analysis", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    row = df[df['company'] == selected_company].iloc[-1]

    st.title(f"🏛️ ניתוח הוליסטי ומבחני קיצון: {selected_company}")

    # --- חלק 1: 5 ה-KPIs הקריטיים [cite: 2026-01-03] ---
    st.subheader("מדדי ליבה ויציבות פיננסית [cite: 2026-01-03]")
    kpi_cols = st.columns(5)
    kpi_cols[0].metric("סולבנסי", f"{row['solvency_ratio']}%", delta_color="normal" if row['solvency_ratio'] >= 150 else "inverse")
    kpi_cols[1].metric("יתרת CSM", f"₪{row['csm_balance']}B")
    kpi_cols[2].metric("מרכיב הפסד", f"₪{row['loss_component']}M")
    kpi_cols[3].metric("ROE", f"{row['roe']}%")
    kpi_cols[4].metric("נזילות", f"{row['liquidity']}x")

    st.divider()

    # --- חלק 2: סימולטור תרחישי קיצון (החלק שהוחזר) ---
    col_sim, col_pie = st.columns([1, 1])
    
    with col_sim:
        st.subheader("🛡️ מנוע תרחישי קיצון (Stress Test)")
        int_slide = st.select_slider("שינוי ריבית (bps)", options=[-100, -50, 0, 50, 100], value=0)
        mkt_slide = st.slider("קריסת שוק המניות (%)", -30, 0, 0)
        
        # חישוב השפעה מבוסס מקדמי הרגישות
        impact = (int_slide/100 * row['int_sens'] * 100) + (mkt_slide/10 * row['mkt_sens'] * 100)
        final_solv = row['solvency_ratio'] + impact
        
        st.metric("סולבנסי מוערך בתרחיש", f"{final_solv:.1f}%", delta=f"{impact:.1f}%")
        if final_solv < 150:
            st.error("⚠️ אזהרה: ירידה מתחת ליעד ההון הניהולי (150%) [cite: 2026-01-03]")

    with col_pie:
        st.subheader("חלוקת CSM לפי מגזרים")
        segments = pd.DataFrame({
            "מגזר": ["חיים וחיסכון", "בריאות", "כללי"],
            "CSM (B)": [row['life_csm'], row['health_csm'], row['general_csm']]
        })
        fig = px.pie(segments, values='CSM (B)', names='מגזר', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- חלק 3: ניתוח דוחות מעמיק (מאזן, רוה"פ, תזרים) ---
    st.subheader("ניתוח דוחות כספיים מורחב")
    tab_pnl, tab_bs, tab_cf = st.tabs(["דוח רווח והפסד", "מאזן ונזילות", "דוח תזרים מזומנים"])

    with tab_pnl:
        c1, c2 = st.columns(2)
        c1.metric("יחס הוצאות (Expense Ratio)", f"{row['expense_ratio']}%")
        c2.metric("יחס משולב (Combined Ratio)", f"{row['combined_ratio']}%")

    with tab_bs:
        st.metric("הון עצמי לסך מאזן", f"{row['equity_to_balance']}%")
        st.info("יחס זה מעיד על רמת המינוף והחוסן המאזני של הקבוצה.")

    with tab_cf:
        st.metric("תזרים מפעילות שוטפת", f"₪{row['operating_cash_flow']}B")
        st.write("תזרים חיובי מפעילות שוטפת מאמת את איכות הרווח החשבונאי.")

except Exception as e:
    st.error(f"שגיאה: ודא שקובץ ה-CSV מכיל את כל העמודות החדשות. {e}")
