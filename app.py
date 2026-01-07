import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# הגדרות מערכת למקום ראשון - יציבות וקריאות
st.set_page_config(page_title="GLOBAL INSURANCE SUPERVISOR AI", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-bottom: 4px solid #007bff; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f8f9fa; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    selected_company = st.sidebar.selectbox("🔍 בחר חברה לביקורת:", df['company'].unique())
    
    # שליפת נתונים היסטוריים למגמות
    c_df = df[df['company'] == selected_company].sort_values(['year', 'quarter'])
    row = c_df.iloc[-1] # רבעון נוכחי
    prev_row = c_df.iloc[-2] if len(c_df) > 1 else row # רבעון קודם

    st.title(f"🏛️ Global Supervision & Risk AI: {selected_company}")
    st.caption(f"ניתוח רגולטורי מתקדם מבוסס IFRS 17 & Solvency II | עדכון: {row['quarter']} {row['year']}")

    # --- 1. Top Insights Bar ---
    st.subheader("💡 AI Insight Engine (Audit Mode)")
    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        solv_delta = row['solvency_ratio'] - prev_row['solvency_ratio']
        if solv_delta > 0:
            st.success(f"שיפור בחוסן ההוני: עלייה של {solv_delta}% מהרבעון הקודם. החברה בונה כרית ביטחון.")
        else:
            st.warning(f"שחיקת הון: ירידה של {abs(solv_delta)}% מהרבעון הקודם. נדרש בירור גורמי השפעה.")
    
    # --- 2. Main Navigation Tabs ---
    tab_kpi, tab_ifrs17, tab_stress, tab_financials = st.tabs([
        "📊 ליבת חוסן (KPIs)", "📈 ניתוח IFRS 17 מגזרי", "🧪 סימולציית Stress Test", "⚖️ עומק דוחות כספיים"
    ])

    # טאב 1: KPIs עם מגמות (Trends)
    with tab_kpi:
        st.subheader("5 מדדי הליבה הקריטיים [cite: 2026-01-03]")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Solvency Ratio", f"{row['solvency_ratio']}%", f"{row['solvency_ratio']-prev_row['solvency_ratio']}%")
        k2.metric("Total CSM", f"₪{row['csm_balance']}B", f"{row['csm_balance']-prev_row['csm_balance']:.1f}B")
        k3.metric("Loss Component", f"₪{row['loss_component']}M", f"{row['loss_component']-prev_row['loss_component']}M", delta_color="inverse")
        k4.metric("ROE", f"{row['roe']}%", f"{row['roe']-prev_row['roe']:.1f}%")
        k5.metric("Liquidity", f"{row['liquidity']}x", f"{row['liquidity']-prev_row['liquidity']:.1f}x")
        
        # גרף מגמה היסטורי - פיצ'ר חובה למקום ראשון
        st.write("**מגמת סולבנסי ו-CSM לאורך זמן:**")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=c_df['quarter'], y=c_df['solvency_ratio'], name="Solvency (%)", line=dict(color='firebrick', width=4)))
        fig_trend.add_trace(go.Bar(x=c_df['quarter'], y=c_df['csm_balance']*10, name="CSM (Scale x10)", opacity=0.3))
        st.plotly_chart(fig_trend, use_container_width=True)

    # טאב 2: IFRS 17 מגזרי עם נוסחאות
    with tab_ifrs17:
        st.subheader("ניתוח מגזרי (Segmental Granularity)")
        st.latex(r"CSM_{Release} = \frac{Amortization}{Total\ CSM} \quad | \quad Strain = \frac{Acquisition\ Cost}{New\ Business}")
        
        seg_table = pd.DataFrame({
            "מגזר": ["חיים וחיסכון", "בריאות", "כללי"],
            "Release Rate": [f"{row['life_release_rate']}%", f"{row['health_release_rate']}%", f"{row['general_release_rate']}%"],
            "New Biz Strain": [f"{row['life_new_biz_strain']}%", f"{row['health_new_biz_strain']}%", f"{row['general_new_biz_strain']}%"]
        })
        st.table(seg_table)
        
        with st.expander("🧐 הנחיית המפקח לניתוח מגזרי"):
            st.info("בחינת ה-Release Rate במגזר החיים: קצב יציב מעיד על ניהול עתודות שמרני ותקין.")

    # טאב 3: Stress Test עם אינטראקציה מלאה
    with tab_stress:
        st.subheader("🧪 סימולטור Stress Test (Solvency II Standards)")
        st.latex(r"Solv_{adj} = Solv_0 + (\Delta Int \cdot Sens_{int}) + (\Delta Mkt \cdot Sens_{mkt})")
        
        c_s1, c_s2 = st.columns([1, 2])
        with c_s1:
            st.write("**הגדר תרחיש שוק:**")
            s_int = st.select_slider("שינוי ריבית (bps)", options=[-100, -50, 0, 50, 100], value=0)
            s_mkt = st.slider("קריסת מניות (%)", -40, 0, 0)
            impact = (s_int/100 * row['int_sens'] * 100) + (s_mkt/10 * row['mkt_sens'] * 100)
            res_solv = row['solvency_ratio'] + impact
            st.metric("סולבנסי בתרחיש", f"{res_solv:.1f}%", delta=f"{impact:.1f}%")

        with c_s2:
            fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=res_solv, 
                gauge={'axis': {'range': [0, 250]}, 'steps': [
                    {'range': [0, 100], 'color': "#ff4b4b"},
                    {'range': [100, 150], 'color': "#ffa500"},
                    {'range': [150, 250], 'color': "#00cc96"}]}))
            st.plotly_chart(fig_gauge, use_container_width=True)

    # טאב 4: דוחות כספיים מלאים
    with tab_financials:
        st.subheader("עומק חשבונאי: מאזן, רוה\"פ ותזרים")
        f1, f2, f3 = st.columns(3)
        with f1:
            st.write("**רווח והפסד**")
            st.metric("Combined Ratio", f"{row['combined_ratio']}%")
            st.latex(r"CR = \frac{Claims + Exp}{Premiums}")
        with f2:
            st.write("**מאזן וחוסן**")
            st.metric("Tier 1 Ratio", f"{row['tier1_ratio']}%")
            st.latex(r"Tier1 = \frac{Core\ Cap}{RWA}")
        with f3:
            st.write("**תזרים מזומנים**")
            st.metric("תזרים מפעילות", f"₪{row['operating_cash_flow']}B")
            st.caption("אימות איכות הרווח (Earnings Quality Check)")

except Exception as e:
    st.error(f"שגיאת מערכת: {e}")
