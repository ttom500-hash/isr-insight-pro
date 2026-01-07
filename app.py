
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Insurance Supervisor Dashboard", layout="wide")

def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    row = df.iloc[-1]
    
    st.title(f"🔍 פיקוח עמוק וקבלת החלטות: {row['company']}")

    # 1. שכבת ה-KPIs הקריטיים [cite: 2026-01-03]
    st.subheader("🚀 מדדי ליבה פיקוחיים")
    kpi = st.columns(5)
    kpi[0].metric("סולבנסי", f"{row['solvency_ratio']}%")
    kpi[1].metric("CSM", f"₪{row['csm_balance']}B")
    kpi[2].metric("ROE", f"{row['roe']}%")
    kpi[3].metric("נזילות", f"{row['liquidity']}x")
    kpi[4].metric("יחס הוצאות", f"{row['expense_ratio']}%")

    st.divider()

    # 2. הוספת "זווית המפקח" - IFRS 17
    st.subheader("🛡️ ניתוח מעמיק לפי מתודולוגיית IFRS 17")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric("New Business Strain", f"{row['new_biz_strain']}%")
        with st.expander("🧐 מה זה אומר?"):
            st.write("**הסבר:** עלות גיוס לקוחות חדשים ביחס לרווחיותם.")
            st.info("💡 **הנחיית המפקח:** אם היחס מעל 10%, יש לבדוק האם החברה מתמחרת פוליסות בהפסד כדי לצמוח.")

    with c2:
        st.metric("CSM Release Rate", f"{row['csm_release_rate']}%")
        with st.expander("🧐 מה זה אומר?"):
            st.write("**הסבר:** קצב הכרת הרווח מה-CSM לתוך הדו\"ח.")
            st.info("💡 **הנחיית המפקח:** קצב גבוה מדי עלול להחליש את עתודות הרווח לעתיד. ודא עקביות.")

    with c3:
        st.metric("CSM to Equity", f"{row['csm_to_equity']}x")
        with st.expander("🧐 מה זה אומר?"):
            st.write("**הסבר:** יחס הרווח הצבור (CSM) אל מול ההון הקיים.")
            st.info("💡 **הנחיית המפקח:** יחס גבוה מ-1.0 מעיד על חברה עם 'מנוע רווח' עתידי חזק מאוד.")

    # 3. שמירה על תרחישי הקיצון והמגזרים (מה שבנינו קודם)
    st.divider()
    col_sim, col_pie = st.columns(2)
    with col_sim:
        st.subheader("🧪 מבחן קיצון (Stress Test)")
        mkt = st.slider("קריסת שוק (%)", -30, 0, 0)
        impact = (mkt/10 * row['mkt_sens'] * 100)
        st.metric("סולבנסי בתרחיש", f"{row['solvency_ratio'] + impact:.1f}%", delta=f"{impact:.1f}%")

    with col_pie:
        st.subheader("חלוקת CSM מגזרית")
        fig = px.pie(values=[row['life_csm'], row['health_csm'], row['general_csm']], 
                     names=["חיים", "בריאות", "כללי"], hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"שגיאה: {e}")
