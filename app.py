import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. הגדרות דף ועיצוב ניאון עתידני
st.set_page_config(page_title="ISR-Insight Pro | חדר מלחמה רגולטורי", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    [data-testid="stMetricValue"] { color: #00f2ff; font-family: 'Courier New', monospace; }
    .sidebar .sidebar-content { background-image: linear-gradient(#161b22, #0b0e14); }
    h1, h2, h3 { color: #00f2ff; text-shadow: 0 0 10px #00f2ff44; }
    </style>
    """, unsafe_allow_html=True)

# 2. טעינת נתונים חסינה
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/database.csv')
        return df
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("❌ תקלה בטעינת הנתונים. וודא שקובץ data/database.csv קיים ותקין.")
    st.stop()

# --- 3. סרגל צד: תרחישים ופילטרים ---
st.sidebar.title("🛠️ סימולטור תרחישים")
year_f = st.sidebar.selectbox("שנה", df['year'].unique())
q_f = st.sidebar.selectbox("רבעון", df[df['year']==year_f]['quarter'].unique())

st.sidebar.markdown("---")
st.sidebar.subheader("🔥 זעזועי שוק")
s_int = st.sidebar.slider("שינוי ריבית (%)", -2.0, 2.0, 0.0, 0.1)
s_mkt = st.sidebar.slider("ירידה בבורסה (%)", 0, 40, 0)
s_lapse = st.sidebar.slider("עלייה בביטולים (%)", 0, 30, 0)
s_quake = st.sidebar.toggle("🚨 תרחיש רעידת אדמה (PML)")

# --- 4. לוגיקה פיננסית: חישוב תרחיש קיצון ---
# נוסחת ההשפעה על הסולבנסי:
# $$NewSolvency = Base + (\Delta Int \times Sens_{int}) - (\Delta Mkt \times Sens_{mkt}) - (\Delta Lapse \times Sens_{lapse})$$

f_df = df[(df['year'] == year_f) & (df['quarter'] == q_f)].copy()

for i, row in f_df.iterrows():
    impact = (s_int * row['int_sensitivity'] * 100) - \
             (s_mkt/10 * row['mkt_sensitivity'] * 100) - \
             (s_lapse/5 * row['lapse_sensitivity'] * 100)
    if s_quake: impact -= 20 # זעזוע הון קבוע לרעידת אדמה
    f_df.at[i, 'adj_solvency'] = row['solvency_ratio'] + impact
    # יחסים פיננסיים נוספים
    f_df.at[i, 'csm_efficiency'] = (row['csm_balance'] / row['total_assets']) * 100
    f_df.at[i, 'loss_ratio'] = (row['loss_component'] / row['total_assets'])

# --- 5. תצוגה ראשית ---
st.title(f"🛡️ ניתוח סיכונים דינמי: {q_f} {year_f}")
st.markdown(f"**תרחיש נבחר:** ריבית {s_int}% | בורסה -{s_mkt}% | ביטולים +{s_lapse}% {'| 🚨 רעידת אדמה' if s_quake else ''}")

# שורת KPIs ענפית
cols = st.columns(4)
cols[0].metric("ממוצע סולבנסי ענפי", f"{f_df['adj_solvency'].mean():.1f}%")
cols[1].metric("סך CSM בענף", f"{f_df['csm_balance'].sum():.1f}B")
cols[2].metric("חשיפה מקסימלית (Loss)", f"{f_df['loss_component'].max()}M")
cols[3].metric("סטטוס מערכתי", "יציב" if f_df['adj_solvency'].mean() > 140 else "סיכון גבוה", delta_color="inverse")

st.markdown("---")

# גרפים מתקדמים
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🧬 פרופיל סיכון רב-ממדי (Radar Chart)")
    # בחירת חברות להשוואה בגרף עכביש
    comps = st.multiselect("בחר חברות להשוואה:", f_df['company'].unique(), default=f_df['company'].unique()[:3])
    
    fig_radar = go.Figure()
    for comp in comps:
        r_data = f_df[f_df['company'] == comp].iloc[0]
        fig_radar.add_trace(go.Scatterpolar(
            r=[r_data['adj_solvency']/2, r_data['csm_efficiency']*5, 100-(r_data['loss_ratio']*10), 80, r_data['adj_solvency']/2],
            theta=['חוסן הון', 'יעילות רווח', 'איכות חיתום', 'נזילות', 'חוסן הון'],
            fill='toself', name=comp
        ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), template="plotly_dark", height=450)
    st.plotly_chart(fig_radar, use_container_width=True)

with col_right:
    st.subheader("📊 השוואת יציבות בתרחיש קיצון")
    # גרף עמודות המשווה בין המצב המקורי למצב לאחר התרחיש
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(name='סולבנסי מקורי', x=f_df['company'], y=f_df['solvency_ratio'], marker_color='#30363d'))
    fig_compare.add_trace(go.Bar(name='לאחר זעזוע', x=f_df['company'], y=f_df['adj_solvency'], marker_color='#00f2ff'))
    fig_compare.update_layout(barmode='group', template="plotly_dark", height=450)
    st.plotly_chart(fig_compare, use_container_width=True)

# טבלת סיכום מקצועית
st.markdown("### 📋 דוח ריכוז נתונים ודירוג יציבות")
def highlight_risk(val):
    color = '#00ff00' if val > 140 else '#ffaa00' if val > 100 else '#ff4b4b'
    return f'
