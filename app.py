import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Insurance Master Supervision Tool", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    selected_company = st.sidebar.selectbox("בחר חברה:", df['company'].unique())
    row = df[df['company'] == selected_company].iloc[-1]

    st.title(f"🏛️ מערכת פיקוח וניתוח הוליסטית: {selected_company}")
    st.info(f"מקור: {row['data_source']} | תקופה: {row['quarter']} {row['year']}")

    # --- חלק 1: 5 ה-KPIs הקריטיים [cite: 2026-01-03] ---
    st.subheader("🚀 מדדי ליבה ויציבות [cite: 2026-01-03]")
    kpi = st.columns(5)
    kpi[0].metric("סולבנסי", f"{row['solvency_ratio']}%", delta_color="normal" if row['solvency_ratio'] >= 150 else "inverse")
    kpi[1].metric("יתרת CSM", f"₪{row['csm_balance']}B")
    kpi[2].metric("מרכיב הפסד", f"₪{row['loss_component']}M")
    kpi[3].metric("ROE", f"{row['roe']}%")
    kpi[4].metric("נזילות", f"{row['liquidity']}x")

    st.divider()

    # --- חלק 2: סימולטור Stress Test וניתוח מגזרי ---
    col_sim, col_pie = st.columns([1, 1])
    
    with col_sim:
        st.subheader("🧪 סימולטור תרחישי קיצון")
        int_slide = st.select_slider("שינוי ריבית (bps)", options=[-100, -50, 0, 50, 100], value=0)
        mkt_slide = st.slider("קריסת שוק המניות (%)", -30, 0, 0)
        impact = (int_slide/100 * row['int_sens'] * 100) + (mkt_slide/10 * row['mkt_sens'] * 100)
        final_solv = row['solvency_ratio'] + impact
        st.metric("סולבנסי בתרחיש", f"{final_solv:.1f}%", delta=f"{impact:.1f}%")
        if final_solv < 150:
            st.error("⚠️ התראה: ירידה מתחת ליעד ההון (150%) [cite: 2026-01-03]")

    with col_pie:
        st.subheader("חלוקת CSM מגזרית")
        fig = px.pie(values=[row['life_csm'], row['health_csm'], row['general_csm']], 
                     names=["חיים וחיסכון", "בריאות", "כללי"], hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- חלק 3: זווית המפקח ו-IFRS 17 (התוספת החדשה) ---
    st.subheader("🛡️ מתודולוגיה פיקוחית IFRS 17")
    reg_col1, reg_col2, reg_col3 = st.columns(3)
    
    with reg_col1:
        st.metric("New Business Strain", f"{row['new_biz_strain']}%")
        with st.expander("🧐 הנחיית המפקח"):
            st.write("בדיקת עלות רכישת פוליסות מול רווח גלום.")
            st.info("אם היחס גבוה, יש לבחון תמחור חסר במוצרים חדשים.")

    with reg_col2:
        st.metric("CSM Release Rate", f"{row['csm_release_rate']}%")
        with st.expander("🧐 הנחיית המפקח"):
            st.write("קצב שחרור רווח עתידי לדו\"ח רווח והפסד.")
            st.info("קצב גבוה מדי עלול להצביע על ניהול רווחים אגרסיבי.")

    with reg_col3:
        st.metric("CSM to Equity", f"{row['csm_to_equity']}x")
        with st.expander("🧐 הנחיית המפקח"):
            st.write("יחס עושר הרווח העתידי אל מול ההון הקיים.")
            st.success("יחס מעל 1.0 מעיד על כרית הון רווחית חזקה לעתיד.")

    st.divider()

    # --- חלק 4: דוחות כספיים (מאזן, תזרים, רוה"פ) ---
    st.subheader("📋 ניתוח דוחות כספיים מורחב")
    t_pnl, t_bs, t_cf = st.tabs(["רווח והפסד", "מאזן", "תזרים מזומנים"])
    
    with t_pnl:
        st.metric("יחס משולב (Combined Ratio)", f"{row['combined_ratio']}%")
        st.metric("יחס הוצאות הנהלה", f"{row['expense_ratio']}%")
    
    with t_bs:
        st.metric("הון עצמי לסך מאזן", f"{row['equity_to_balance']}%")
    
    with t_cf:
        st.metric("תזרים מפעילות שוטפת", f"₪{row['operating_cash_flow']}B")

except Exception as e:
    st.error(f"שגיאה בטעינה: ודא שה-CSV מעודכן. {e}")
