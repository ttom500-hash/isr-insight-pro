import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# עיצוב דף מתקדם
st.set_page_config(page_title="ISR-Insight Pro | Stress Test Simulator", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: white; }
    .stSlider [data-baseweb="slider"] { margin-bottom: 20px; }
    .metric-card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border-left: 5px solid #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv('data/database.csv')

df = load_data()

st.title("🛡️ סימולטור פיקוח וניתוח תרחישי קיצון")

# --- סרגל צד: פילטרים ותרחישים ---
st.sidebar.header("🔍 פילטרים ותקופות")
year_filter = st.sidebar.selectbox("שנה", df['year'].unique())
quarter_filter = st.sidebar.selectbox("רבעון", df[df['year']==year_filter]['quarter'].unique())

st.sidebar.markdown("---")
st.sidebar.header("🧪 סימולטור תרחישי קיצון")
s_interest = st.sidebar.slider("שינוי בריבית (%)", -2.0, 2.0, 0.0, 0.1)
s_market = st.sidebar.slider("ירידה בשוק המניות (%)", 0, 30, 0)
s_lapse = st.sidebar.slider("עלייה בשיעור ביטולים (%)", 0, 20, 0)
s_quake = st.sidebar.checkbox("תרחיש רעידת אדמה (זעזוע הון)")

# עיבוד הנתונים לפי הפילטר והתרחיש
filtered_df = df[(df['year'] == year_filter) & (df['quarter'] == quarter_filter)].copy()

# חישוב השפעת תרחישים (לוגיקה רגולטורית)
for index, row in filtered_df.iterrows():
    impact = (s_interest * row['int_sensitivity'] * 100) - (s_market/10 * row['mkt_sensitivity'] * 100) - (s_lapse/5 * row['lapse_sensitivity'] * 100)
    if s_quake: impact -= 15 # רעידת אדמה מורידה 15% מהסולבנסי כברירת מחדל
    filtered_df.at[index, 'adjusted_solvency'] = row['solvency_ratio'] + impact

# --- תצוגה ראשית ---
st.subheader(f"סטטוס ענפי - {quarter_filter} {year_filter}")

# תרשים מכ"ם (Radar) להשוואת חברות
st.markdown("### 🧬 DNA של סיכוני חברות (השוואה רב-ממדית)")
categories = ['חוסן הון', 'רווחיות (CSM)', 'יעילות', 'שמרנות', 'עמידות לזעזוע']

fig_radar = go.Figure()
for _, row in filtered_df.iterrows():
    # נרמול נתונים לגרף המכ"ם
    r_values = [row['adjusted_solvency']/2, row['csm_balance']*5, 
                (row['csm_balance']/row['total_assets'])*100, 
                100 - (row['loss_component']/10), row['adjusted_solvency']/2]
    
    fig_radar.add_trace(go.Scatterpolar(
          r=r_values, theta=categories, fill='toself', name=row['company']
    ))

fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        template="plotly_dark", showlegend=True, height=500)
st.plotly_chart(fig_radar, use_container_width=True)



# טבלת נתונים חיה עם צבעים
st.markdown("### 📋 נתונים מותאמים לתרחיש")
def color_solvency(val):
    color = '#00ff00' if val > 140 else '#ffaa00' if val > 100 else '#ff0000'
    return f'color: {color}; font-weight: bold'

styled_df = filtered_df[['company', 'solvency_ratio', 'adjusted_solvency', 'csm_balance', 'loss_component']]
st.table(styled_df.style.applymap(color_solvency, subset=['adjusted_solvency']))

# יחסים פיננסיים נוספים
st.markdown("---")
st.markdown("### 📊 יחסים פיננסיים נבחרים")
col1, col2, col3 = st.columns(3)
with col1:
    avg_sol = filtered_df['adjusted_solvency'].mean()
    st.metric("ממוצע סולבנסי ענפי (מותאם)", f"{avg_sol:.1f}%")
with col2:
    total_csm = filtered_df['csm_balance'].sum()
    st.metric("סך הון עתידי בענף (CSM)", f"{total_csm:.1f}B ₪")
with col3:
    st.info("יחס הון/סיכון משקף את יכולת הספיגה של הענף בתרחיש הנבחר.")
