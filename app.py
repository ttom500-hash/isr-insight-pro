import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. הגדרות דף ועיצוב
st.set_page_config(page_title="Insurance Insight Pro", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e1e4e8; }
    h1, h2, h3 { color: #1a3a5a; text-align: right; }
    .stMarkdown { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# 2. פונקציית טעינת נתונים חסינה
def load_data():
    # נתיבים אפשריים לקובץ (מקומי ובשרת)
    paths = ['data/database.csv', 'database.csv']
    df = None
    
    for path in paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                break
            except:
                continue
    
    # אם לא נמצא קובץ, ניצור נתוני ברירת מחדל כדי שהאפליקציה לא תהיה "דף חלק"
    if df is None:
        data = {
            'company': ['Phoenix', 'Harel'],
            'year': [2025, 2025],
            'quarter': ['Q3', 'Q3'],
            'solvency_ratio': [185, 172],
            'csm_balance': [12.4, 11.8],
            'loss_component': [150, 190],
            'roe': [14.2, 12.5],
            'liquidity': [1.2, 1.3],
            'combined_ratio': [92.5, 94.2],
            'life_csm': [6.5, 5.9], 'health_csm': [3.2, 2.9], 'general_csm': [2.7, 3.0],
            'int_sens': [0.14, 0.15], 'mkt_sens': [0.11, 0.10],
            'tier1_ratio': [162, 152], 'equity_to_balance': [8.4, 7.9], 'operating_cash_flow': [1.8, 1.5],
            'life_release_rate': [7.2, 7.5], 'health_release_rate': [9.1, 9.5], 'general_release_rate': [12.5, 13.0],
            'life_new_biz_strain': [3.1, 3.5], 'health_new_biz_strain': [5.2, 5.5], 'general_new_biz_strain': [8.4, 9.0],
            'csm_to_equity': [1.4, 1.2]
        }
        df = pd.DataFrame(data)
        st.sidebar.warning("מריץ נתוני דמו - קובץ ה-CSV לא נמצא בתיקיית data")
    return df

df = load_data()

# 3. בניית הממשק
st.sidebar.title("🛡️ לוח בקרה")
company = st.sidebar.selectbox("בחר חברה:", df['company'].unique())

# סינון נתונים
c_data = df[df['company'] == company].iloc[-1]

st.title(f"🏛️ ניתוח פיננסי: {company}")
st.divider()

# טאבים
t1, t2, t3, t4 = st.tabs(["📊 מדדי ליבה", "🧬 IFRS 17", "🏁 השוואת שוק", "🧪 Stress Test"])

with t1:
    st.subheader("5 מדדי KPI קריטיים")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Solvency", f"{c_data['solvency_ratio']}%")
    col2.metric("CSM Balance", f"₪{c_data['csm_balance']}B")
    col3.metric("ROE", f"{c_data['roe']}%")
    col4.metric("Liquidity", f"{c_data['liquidity']}x")
    col5.metric("Combined Ratio", f"{c_data['combined_ratio']}%")

with t2:
    st.subheader("פירוט CSM מגזרי")
    fig_pie = px.pie(values=[c_data['life_csm'], c_data['health_csm'], c_data['general_csm']], 
                     names=['חיים', 'בריאות', 'כללי'], hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with t3:
    st.subheader("השוואת עמיתים (Benchmarking)")
    fig_scatter = px.scatter(df, x="solvency_ratio", y="roe", size="csm_balance", 
                             color="company", text="company", 
                             labels={"solvency_ratio": "חוסן (Solvency)", "roe": "רווחיות (ROE)"})
    st.plotly_chart(fig_scatter, use_container_width=True)

with t4:
    st.subheader("סימולציית רגישות הון")
    s_mkt = st.slider("קריסת שוק המניות (%)", -40, 0, 0)
    impact = (s_mkt/10 * c_data['mkt_sens'] * 100)
    new_solv = c_data['solvency_ratio'] + impact
    st.metric("Solvency בתרחיש", f"{new_solv:.1f}%", f"{impact:.1f}%")
