
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. הגדרות ועיצוב
st.set_page_config(page_title="GLOBAL INSIGHT PRO | Insurance AI", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e1e4e8; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .red-flag { background-color: #fff5f5; border-right: 5px solid #ff4b4b; padding: 15px; border-radius: 5px; margin: 10px 0; color: #c53030; font-weight: bold; text-align: right; }
    .success-flag { background-color: #f0fff4; border-right: 5px solid #38a169; padding: 15px; border-radius: 5px; margin: 10px 0; color: #2f855a; font-weight: bold; text-align: right; }
    .formula-box { background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-family: 'Courier New', monospace; direction: ltr; }
    h1, h2, h3 { text-align: right; }
    .stMarkdown { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# 2. טעינת נתונים חסינה
def load_data():
    paths = ['data/database.csv', 'database.csv']
    df = None
    for path in paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                break
            except: continue
    if df is None:
        st.error("קובץ הנתונים לא נמצא! ודא שקיים database.csv בתיקיית data")
        st.stop()
    return df

df = load_data()

# 3. תפריט צידי ובחירת חברה
st.sidebar.title("🛡️ ניהול סיכונים ופיקוח")
selected_company = st.sidebar.selectbox("בחר חברה לניתוח:", df['company'].unique())
c_data = df[df['company'] == selected_company].iloc[-1]
market_avg = df.mean(numeric_only=True)

st.title(f"🏛️ Insurance Insight Pro: {selected_company}")
st.caption(f"ניתוח עומק לפי תקן IFRS 17 | {c_data['quarter']} {c_data['year']}")

# --- 🚩 דגלים אדומים ותובנות AI (שכבת הפיקוח) ---
st.subheader("🤖 AI Regulatory Insights & Red Flags")
col_ins1, col_ins2 = st.columns(2)

with col_ins1:
    # לוגיקה לדגלים אדומים
    if c_data['solvency_ratio'] < 150:
        st.markdown(f"<div class='red-flag'>🚩 דגל אדום: יחס סולבנסי ({c_data['solvency_ratio']}%) נמוך מיעד הפיקוח (150%). נדרשת תוכנית הון.</div>", unsafe_allow_html=True)
    elif c_data['solvency_ratio'] > 180:
        st.markdown(f"<div class='success-flag'>✅ חוסן גבוה: יחס סולבנסי מאפשר חלוקת דיבידנד בכפוף לאישור מפקח.</div>", unsafe_allow_html=True)
    
    if c_data['combined_ratio'] > 100:
        st.markdown(f"<div class='red-flag'>🚩 דגל אדום: הפסד חיתומי (Combined Ratio > 100%). המודל העסקי נשען על רווחי השקעות בלבד.</div>", unsafe_allow_html=True)

with col_ins2:
    if c_data['roe'] > market_avg['roe']:
        st.markdown(f"<div class='success-flag'>📈 ביצועי יתר: תשואה להון ({c_data['roe']}%) גבוהה מממוצע השוק ({market_avg['roe']:.1f}%).</div>", unsafe_allow_html=True)
    if c_data['loss_component'] > market_avg['loss_component']:
        st.markdown(f"<div class='red-flag'>⚠️ רגישות גבוהה: מרכיב ההפסד (Loss Component) גבוה מהממוצע. קיימת חשיפה לחוזים מכבידים.</div>", unsafe_allow_html=True)

st.divider()

# 4. טאבים לניתוח מפורט
tabs = st.tabs(["📊 5 KPIs קריטיים", "🧬 ניתוח IFRS 17", "🏁 השוואת שוק", "🧪 Stress Test"])

# טאב 1: KPIs עם הסברים מפורטים
with tabs[0]:
    st.subheader("ניתוח 5 מדדי מפתח (KPIs)")
    cols = st.columns(5)
    
    kpis = [
        ("Solvency II", f"{c_data['solvency_ratio']}%", "יציבות הונית", r"Ratio = \frac{Eligible\ Funds}{SCR}"),
        ("CSM Balance", f"₪{c_data['csm_balance']}B", "רווח עתידי גלום", r"CSM_{t} = CSM_{t-1} + NB - Rel"),
        ("ROE", f"{c_data['roe']}%", "יעילות הון", r"ROE = \frac{Net\ Income}{Equity}"),
        ("Loss Component", f"₪{c_data['loss_component']}M", "חוזים מכבידים", "Onerous Contracts"),
        ("Liquidity", f"{c_data['liquidity']}x", "נזילות מיידית", r"Ratio = \frac{Liquid\ Assets}{Liabilities}")
    ]
    
    for i, (name, val, desc, formula) in enumerate(kpis):
        with cols[i]:
            st.metric(name, val)
            st.caption(f"**{desc}**")
            with st.expander("הסבר טכני"):
                st.latex(formula)
                st.write(f"זהו מדד המפתח לבחינת {desc}. חריגה מממוצע השוק דורשת הסבר בדוח הדירקטוריון.")

# טאב 2: IFRS 17 מגזרי
with tabs[1]:
    st.subheader("🧬 התפלגות ורווחיות לפי מגזרי פעילות")
    col_t, col_p = st.columns([2, 1])
    with col_t:
        st.write("**מדדי יעילות חיתומית (Underwriting Efficiency)**")
        seg_data = pd.DataFrame({
            "מגזר": ["חיים וחיסכון", "בריאות", "ביטוח כללי"],
            "קצב שחרור CSM": [f"{c_data['life_release_rate']}%", f"{c_data['health_release_rate']}%", f"{c_data['general_release_rate']}%"],
            "עצימות הון (Strain)": [f"{c_data['life_new_biz_strain']}%", f"{c_data['health_new_biz_strain']}%", f"{c_data['general_new_biz_strain']}%"]
        })
        st.table(seg_data)
    with col_p:
        fig_pie = px.pie(values=[c_data['life_csm'], c_data['health_csm'], c_data['general_csm']], 
                         names=['חיים', 'בריאות', 'כללי'], hole=0.4, title="פיזור CSM")
        st.plotly_chart(fig_pie, use_container_width=True)

# טאב 3: Benchmarking (השוואה לחברות אחרות)
with tabs[2]:
    st.subheader("🏁 מיקום החברה מול עמיתיה בשוק")
    fig_bench = px.scatter(df, x="solvency_ratio", y="roe", size="csm_balance", color="company",
                           text="company", labels={"solvency_ratio": "יחס סולבנסי (%)", "roe": "תשואה להון (ROE)"})
    fig_bench.update_traces(textposition='top center')
    # הוספת קווי ממוצע להשוואה
    fig_bench.add_vline(x=market_avg['solvency_ratio'], line_dash="dash", line_color="gray", annotation_text="ממוצע סולבנסי")
    fig_bench.add_hline(y=market_avg['roe'], line_dash="dash", line_color="gray", annotation_text="ממוצע ROE")
    st.plotly_chart(fig_bench, use_container_width=True)

# טאב 4: Stress Test
with tabs[3]:
    st.subheader("🧪 סימולציית תרחישי קיצון (Stress Test)")
    st.write("כיצד תנודות בשוק ישפיעו על יחס הסולבנסי של החברה?")
    s_mkt = st.slider("ירידה בשוק המניות (%)", -40, 0, 0)
    impact = (s_mkt/10 * c_data['mkt_sens'] * 100)
    new_solv = c_data['solvency_ratio'] + impact
    
    c1, c2 = st.columns(2)
    c1.metric("סולבנסי חזוי", f"{new_solv:.1f}%", f"{impact:.1f}%")
    
    fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=new_solv,
        gauge={'axis': {'range': [0, 250]}, 'steps': [
            {'range': [0, 100], 'color': "#ff4b4b"},
            {'range': [100, 150], 'color': "#ffa500"},
            {'range': [150, 250], 'color': "#00cc96"}]}))
    st.plotly_chart(fig_gauge, use_container_width=True)
