import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# הגדרות עמוד ועיצוב יוקרתי
st.set_page_config(page_title="INSIGHT PRO | Global Supervision", layout="wide", initial_sidebar_state="expanded")

# CSS להתאמת עיצוב מקצועי
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 20px; border-radius: 15px; border: 1px solid #30363d; }
    .stTab { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

try:
    df = load_data()
    selected_company = st.sidebar.selectbox("🏢 בחר ישות מבוטחת:", df['company'].unique())
    row = df[df['company'] == selected_company].iloc[-1]

    # כותרת ראשית מעוצבת
    st.title("🛡️ Insurance Supervision & Risk Management")
    st.subheader(f"ניתוח עומק רגולטורי - {selected_company} | רבעון {row['quarter']} {row['year']}")
    
    # שורת מצב מהירה (Status Bar)
    status_cols = st.columns(4)
    with status_cols[0]:
        st.success("✅ יציבות הון: תקינה")
    with status_cols[1]:
        st.info(f"📊 מקור: {row['data_source']}")

    st.divider()

    # --- מבנה לשוניות (Architecture) ---
    tab_executive, tab_ifrs17, tab_stress, tab_risk = st.tabs([
        "💎 תמצית מנהלים (KPIs)", 
        "📈 ניתוח IFRS 17 מגזרי", 
        "🧪 תרחישי קיצון", 
        "⚠️ מפת סיכונים (Heatmap)"
    ])

    # --- לשונית 1: תמצית מנהלים ---
    with tab_executive:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Solvency Ratio", f"{row['solvency_ratio']}%", delta="Target: 150%")
        col2.metric("Total CSM", f"₪{row['csm_balance']}B")
        col3.metric("Tier 1 Capital", f"{row['tier1_ratio']}%")
        col4.metric("ROE", f"{row['roe']}%")
        col5.metric("Net Liquidity", f"{row['liquidity']}x")
        
        st.subheader("ניתוח חוסן פיננסי משלים")
        c1, c2, c3 = st.columns(3)
        c1.write(f"**הון עצמי למאזן:** {row['equity_to_balance']}%")
        c2.write(f"**יחס משולב:** {row['combined_ratio']}%")
        c3.write(f"**תזרים מפעילות:** ₪{row['operating_cash_flow']}B")

    # --- לשונית 2: IFRS 17 מגזרי ---
    with tab_ifrs17:
        st.subheader("ניתוח רווחיות ויעילות לפי מגזרי פעילות")
        
        # טבלה מעוצבת
        seg_df = pd.DataFrame({
            "מגזר": ["חיים", "בריאות", "כללי"],
            "CSM (B)": [row['life_csm'], row['health_csm'], row['general_csm']],
            "Release Rate": [f"{row['life_release_rate']}%", f"{row['health_release_rate']}%", f"{row['general_release_rate']}%"],
            "New Biz Strain": [f"{row['life_new_biz_strain']}%", f"{row['health_new_biz_strain']}%", f"{row['general_new_biz_strain']}%"]
        })
        st.dataframe(seg_df, use_container_width=True)
        
        # גרף השוואתי
        fig_segments = go.Figure()
        fig_segments.add_trace(go.Bar(name='Release Rate', x=seg_df['מגזר'], y=[row['life_release_rate'], row['health_release_rate'], row['general_release_rate']], marker_color='#00cc96'))
        fig_segments.add_trace(go.Bar(name='New Biz Strain', x=seg_df['מגזר'], y=[row['life_new_biz_strain'], row['health_new_biz_strain'], row['general_new_biz_strain']], marker_color='#ef553b'))
        fig_segments.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig_segments, use_container_width=True)

    # --- לשונית 3: תרחישי קיצון ---
    with tab_stress:
        st.subheader("סימולציית רגישות הון (Solvency Stress Test)")
        col_s1, col_s2 = st.columns([1, 2])
        
        with col_s1:
            st.write("כוונן פרמטרים:")
            s_int = st.slider("שינוי ריבית (bps)", -200, 200, 0)
            s_mkt = st.slider("קריסת שוק המניות (%)", -40, 0, 0)
            
            impact = (s_int/100 * row['int_sens'] * 100) + (s_mkt/10 * row['mkt_sens'] * 100)
            final_solv = row['solvency_ratio'] + impact
        
        with col_s2:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = final_solv,
                delta = {'reference': 150, 'position': "top"},
                gauge = {
                    'axis': {'range': [0, 250]},
                    'bar': {'color': "#00ffcc"},
                    'steps': [
                        {'range': [0, 100], 'color': "#ff4b4b"},
                        {'range': [100, 150], 'color': "#ffa500"},
                        {'range': [150, 250], 'color': "#00cc96"}]}))
            fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=400)
            st.plotly_chart(fig_gauge, use_container_width=True)

    # --- לשונית 4: מפת סיכונים (Heatmap) ---
    with tab_risk:
        st.subheader("לוח בקרה לניהול סיכונים (Risk Heatmap)")
        
        # בניית מפה חזותית של סיכונים
        risk_data = {
            "סוג סיכון": ["שוק", "אשראי", "חיתום"],
            "ציון": [row['market_risk_score'], row['credit_risk_score'], row['underwriting_risk_score']]
        }
        
        def get_risk_label(score):
            if score == 1: return "🟢 נמוך"
            if score == 2: return "🟡 בינוני"
            return "🔴 גבוה"

        r_cols = st.columns(3)
        for i, risk in enumerate(risk_data["סוג סיכון"]):
            r_cols[i].metric(risk, get_risk_label(risk_data["ציון"][i]))
        
        st.info("💡 **הערת פיקוח:** מפת הסיכונים מבוססת על מתודולוגיית ORSA (Own Risk and Solvency Assessment).")

except Exception as e:
    st.error(f"שגיאה קריטית: {e}")
