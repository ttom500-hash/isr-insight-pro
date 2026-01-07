import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. הגדרות מערכת ועיצוב (High-End UI)
st.set_page_config(page_title="GLOBAL INSIGHT PRO | Insurance AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e1e4e8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .formula-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-right: 5px solid #007bff; margin: 10px 0; font-family: serif; }
    h1, h2, h3 { color: #1a3a5a; }
    </style>
    """, unsafe_allow_html=True)

# 2. טעינת נתונים מהמחסן
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/database.csv')
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

df = load_data()

if df is not None:
    # סרגל צד לבחירת חברה
    st.sidebar.title("🛡️ בקרת מפקח")
    selected_company = st.sidebar.selectbox("בחר חברה לניתוח עומק:", df['company'].unique())
    
    # שליפת נתונים
    c_df = df[df['company'] == selected_company].sort_values(['year', 'quarter'])
    row = c_df.iloc[-1]
    prev_row = c_df.iloc[-2] if len(c_df) > 1 else row

    st.title(f"🏛️ Insurance Insight Pro: {selected_company}")
    st.caption(f"מערכת DSS | תקן IFRS 17 & Solvency II | {row['quarter']} {row['year']}")

    # --- שכבה 1: AI Executive Insights ---
    st.subheader("🤖 AI Risk & Performance Insights")
    
    risk_score = (row['solvency_ratio']/2.5 + row['roe']*2 + (1/row['combined_ratio'])*4000) / 10
    
    c_score, c_insight = st.columns([1, 2])
    with c_score:
        st.metric("Resilience Score (0-100)", f"{risk_score:.1f}")
    with c_insight:
        market_avg_solv = df['solvency_ratio'].mean()
        if row['solvency_ratio'] >= market_avg_solv:
            st.success(f"החברה מציגה חוסן הוני גבוה מממוצע השוק ({market_avg_solv:.1f}%).")
        else:
            st.warning(f"יחס הסולבנסי נמוך מממוצע השוק. נדרש מעקב רגולטורי.")

    st.divider()

    # --- שכבה 2: ניווט בטאבים ---
    tabs = st.tabs(["📊 KPIs", "🧬 IFRS 17 מגזרי", "🧪 Stress Test", "🏁 השוואת שוק", "⚖️ דוחות כספיים"])

    # טאב 1: KPIs
    with tabs[0]:
        st.subheader("מדדי ליבה קריטיים")
        cols = st.columns(5)
        kpi_list = [
            ("Solvency Ratio", f"{row['solvency_ratio']}%", row['solvency_ratio']-prev_row['solvency_ratio'], r"Ratio = \frac{Eligible\ Funds}{SCR}"),
            ("Total CSM", f"₪{row['csm_balance']}B", row['csm_balance']-prev_row['csm_balance'], r"CSM_{t} = CSM_{t-1} + NB - Rel"),
            ("Loss Component", f"₪{row['loss_component']}M", row['loss_component']-prev_row['loss_component'], "Onerous Contracts"),
            ("ROE", f"{row['roe']}%", row['roe']-prev_row['roe'], r"ROE = \frac{Net\ Income}{Equity}"),
            ("Liquidity", f"{row['liquidity']}x", row['liquidity']-prev_row['liquidity'], r"Ratio = \frac{Liquid\ Assets}{Liabilities}")
        ]
        for i, (name, val, delta, formula) in enumerate(kpi_list):
            with cols[i]:
                st.metric(name, val, f"{delta:.1f}")
                with st.expander("🔬 מתודולוגיה"):
                    st.latex(formula)

    # טאב 2: מגזרים
    with tabs[1]:
        st.subheader("ניתוח רווחיות לפי מגזר פעילות")
        seg_df = pd.DataFrame({
            "מדד פיננסי": ["Release Rate", "New Business Strain"],
            "חיים": [f"{row['life_release_rate']}%", f"{row['life_new_biz_strain']}%"],
            "בריאות": [f"{row['health_release_rate']}%", f"{row['health_new_biz_strain']}%"],
            "כללי": [f"{row['general_release_rate']}%", f"{row['general_new_biz_strain']}%"]
        })
        st.table(seg_df)
        fig_pie = px.pie(values=[row['life_csm'], row['health_csm'], row['general_csm']], 
                         names=["חיים", "בריאות", "כללי"], hole=0.4, title="פיזור CSM")
        st.plotly_chart(fig_pie, use_container_width=True)

    # טאב 3: Stress Test
    with tabs[2]:
        st.subheader("🧪 סימולציית רגישות הון")
        c_s1, c_s2 = st.columns([1, 2])
        with c_s1:
            s_int = st.select_slider("ריבית (bps)", options=[-100, -50, 0, 50, 100], value=0)
            s_mkt = st.slider("קריסת מניות (%)", -40, 0, 0)
            impact = (s_int/100 * row['int_sens'] * 100) + (s_mkt/10 * row['mkt_sens'] * 100)
            res_solv = row['solvency_ratio'] + impact
            st.metric("Solvency בתרחיש", f"{res_solv:.1f}%", f"{impact:.1f}%")
        with c_s2:
            fig_g = go.Figure(go.Indicator(mode="gauge+number", value=res_solv, 
                gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 150], 'color': "orange"}, {'range': [150, 250], 'color': "green"}]}))
            st.plotly_chart(fig_g, use_container_width=True)

    # טאב 4: השוואת שוק
    with tabs[3]:
        st.subheader("🏁 Peer Group Benchmarking")
        fig_scatter = px.scatter(df, x="solvency_ratio", y="roe", size="csm_balance", color="company",
