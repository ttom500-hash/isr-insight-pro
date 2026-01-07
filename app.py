import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Insurance Executive Analytics Pro", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
    row = df[df['company'] == selected_company].iloc[-1]

    st.title(f"🏛️ מערכת פיקוח הוליסטית: {selected_company}")
    st.caption(f"מקור: {row['data_source']} | עדכון אחרון: {row['quarter']} {row['year']}")

    # --- 1. חמשת מדדי הליבה הקריטיים [cite: 2026-01-03] ---
    st.subheader("🚀 מדדי ליבה ויציבות פיננסית [cite: 2026-01-03]")
    kpi = st.columns(5)
    kpi[0].metric("סולבנסי", f"{row['solvency_ratio']}%", delta_color="normal" if row['solvency_ratio'] >= 150 else "inverse")
    kpi[1].metric("יתרת CSM", f"₪{row['csm_balance']}B")
    kpi[2].metric("מרכיב הפסד", f"₪{row['loss_component']}M")
    kpi[3].metric("ROE", f"{row['roe']}%")
    kpi[4].metric("נזילות", f"{row['liquidity']}x")

    st.divider()

    # --- 2. סימולטור תרחישי קיצון (Stress Test) ---
    col_sim, col_pie = st.columns([1, 1])
    with col_sim:
        st.subheader("🧪 מנוע תרחישי קיצון (Stress Test)")
        int_slide = st.select_slider("שינוי ריבית (bps)", options=[-100, -50, 0, 50, 100], value=0)
        mkt_slide = st.slider("קריסת שוק המניות (%)", -30, 0, 0)
        
        impact = (int_slide/100 * row['int_sens'] * 100) + (mkt_slide/10 * row['mkt_sens'] * 100)
        final_solv = row['solvency_ratio'] + impact
        st.metric("סולבנסי מותאם לתרחיש", f"{final_solv:.1f}%", delta=f"{impact:.1f}%")
        
        if final_solv < 150:
            st.error("⚠️ אזהרה: ירידה מתחת ליעד ההון (150%) [cite: 2026-01-03]")

    with col_pie:
        st.subheader("פיזור CSM (מיליארד ש\"ח)")
        fig_pie = px.pie(values=[row['life_csm'], row['health_csm'], row['general_csm']], 
                         names=["חיים וחיסכון", "בריאות", "כללי"], hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # --- 3. ניתוח IFRS 17 מגזרי עמוק (התוספת החדשה) ---
    st.subheader("🛡️ ניתוח IFRS 17 מעמיק לפי מגזרי פעילות")
    
    # טבלת יחסים מגזרית
    segment_metrics = pd.DataFrame({
        "מדד פיקוחי (IFRS 17)": ["CSM Release Rate", "New Business Strain"],
        "חיים וחיסכון": [f"{row['life_release_rate']}%", f"{row['life_new_biz_strain']}%"],
        "בריאות": [f"{row['health_release_rate']}%", f"{row['health_new_biz_strain']}%"],
        "ביטוח כללי": [f"{row['general_release_rate']}%", f"{row['general_new_biz_strain']}%"]
    })
    st.table(segment_metrics)

    # גרף השוואת ביצועים מגזריים
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(name='קצב שחרור רווח (Release)', x=['חיים', 'בריאות', 'כללי'], 
                             y=[row['life_release_rate'], row['health_release_rate'], row['general_release_rate']]))
    fig_bar.add_trace(go.Bar(name='עצימות הון חדש (Strain)', x=['חיים', 'בריאות', 'כללי'], 
                             y=[row['life_new_biz_strain'], row['health_new_biz_strain'], row['general_new_biz_strain']]))
    fig_bar.update_layout(title="השוואת יעילות ורווחיות מגזרית (IFRS 17)", barmode='group')
    st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("🧐 הנחיות המפקח לניתוח הממצאים"):
        st.write(f"**CSM to Equity:** יחס הקבוצה עומד על **{row['csm_to_equity']}x**, המעיד על פוטנציאל רווח עתידי חזק ביחס להון הקיים.")
        st.info("שימו לב להבדלים ב-Strain: מגזר המציג עצימות הון גבוהה דורש בחינה של מודל התמחור והעמלות.")

    st.divider()

    # --- 4. ניתוח דוחות כספיים (רוה"פ, מאזן, תזרים) ---
    st.subheader("📋 ניתוח דוחות כספיים משלים")
    t_pnl, t_bs, t_cf = st.tabs(["דוח רווח והפסד", "מאזן ונזילות", "דוח תזרים מזומנים"])
    
    with t_pnl:
        st.metric("יחס משולב (Combined Ratio)", f"{row['combined_ratio']}%", help="רווחיות חיתומית בביטוח כללי")
        st.metric("יחס הוצאות הנהלה", f"{row['expense_ratio']}%")
    
    with t_bs:
        st.metric("הון עצמי לסך מאזן", f"{row['equity_to_balance']}%")
        st.write("יחס זה משמש לבחינת רמת המינוף של הקבוצה ביחס לנכסים המנוהלים.")
    
    with t_cf:
        st.metric("תזרים מפעילות שוטפת", f"₪{row['operating_cash_flow']}B")
        st.write("תזרים חיובי מאשר כי הרווחיות החשבונאית מגובה במזומנים זמינים.")

except Exception as e:
    st.error(f"שגיאה קריטית: ודא שקובץ ה-CSV ב-GitHub מכיל את כל העמודות החדשות. פירוט: {e}")
