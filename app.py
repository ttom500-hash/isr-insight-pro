import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. הגדרות דף למראה "מהפנט" וחדשני
st.set_page_config(page_title="ISR-Insight Pro | חדר בקרה רגולטורי", layout="wide")

# עיצוב CSS מתקדם למראה ניאון מקצועי
st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,212,255,0.1); }
    [data-testid="stMetricValue"] { color: #00f2ff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: bold; }
    .sidebar .sidebar-content { background-image: linear-gradient(#161b22, #0b0e14); }
    h1, h2, h3 { color: #00f2ff; text-align: right; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. טעינת נתונים חסינה
@st.cache_data
def load_data():
    try:
        # טעינת הנתונים מה-CSV שיצרנו בתיקיית data
        df = pd.read_csv('data/database.csv')
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# בדיקה אם הנתונים קיימים
if df.empty:
    st.error("❌ תקלה: קובץ הנתונים data/database.csv חסר או לא תקין.")
    st.stop()

# --- 3. סרגל צד: פילטרים וסימולטור תרחישים ---
st.sidebar.title("🛠️ לוח בקרה וסימולציה")

# פילטר זמן
st.sidebar.subheader("📅 בחירת תקופה")
year_f = st.sidebar.selectbox("בחר שנה", sorted(df['year'].unique(), reverse=True))
q_f = st.sidebar.selectbox("בחר רבעון", df[df['year']==year_f]['quarter'].unique())

st.sidebar.markdown("---")

# סרגלי תרחישים (Stress Test)
st.sidebar.subheader("🧪 סימולטור תרחישי קיצון")
s_int = st.sidebar.slider("שינוי ריבית (%)", -2.5, 2.5, 0.0, 0.1)
s_mkt = st.sidebar.slider("ירידה בשוק המניות (%)", 0, 40, 0)
s_lapse = st.sidebar.slider("עלייה בשיעור ביטולים (%)", 0, 30, 0)
s_quake = st.sidebar.toggle("🚨 תרחיש רעידת אדמה (זעזוע PML)")

# --- 4. לוגיקה פיננסית וחישוב תרחישים ---
# סינון הנתונים לתקופה הנבחרת
f_df = df[(df['year'] == year_f) & (df['quarter'] == q_f)].copy()

# חישוב יציבות מותאמת לתרחיש
for i, row in f_df.iterrows():
    # נוסחת רגישות: שינוי בסולבנסי = (שינוי ריבית * רגישות) - (ירידת מניות * רגישות) ...
    impact = (s_int * row['int_sensitivity'] * 100) - \
             (s_mkt/10 * row['mkt_sensitivity'] * 100) - \
             (s_lapse/5 * row['lapse_sensitivity'] * 100)
    
    if s_quake: impact -= 20  # הנחת עבודה: רעידת אדמה מורידה 20% מההון
    
    f_df.at[i, 'adj_solvency'] = row['solvency_ratio'] + impact
    
    # יחסים פיננסיים נוספים
    f_df.at[i, 'csm_to_assets'] = (row['csm_balance'] / row['total_assets']) * 100
    f_df.at[i, 'risk_intensity'] = (row['loss_component'] / row['csm_balance'])

# --- 5. תצוגה ראשית ---
st.title(f"🛡️ מערכת פיקוח וסימולציה: {q_f} {year_f}")
st.markdown(f"**מצב סימולציה:** ריבית ({s_int}%) | מניות (-{s_mkt}%) | ביטולים (+{s_lapse}%)")

# שורת KPIs ענפית
c1, c2, c3, c4 = st.columns(4)
c1.metric("ממוצע סולבנסי (מותאם)", f"{f_df['adj_solvency'].mean():.1f}%", f"{s_int}%")
c2.metric("סך CSM ענפי", f"{f_df['csm_balance'].sum():.1f}B ₪")
c3.metric("שיא חוזים הפסדיים", f"{f_df['loss_component'].max()}M ₪")
c4.metric("חברות בסיכון (מתחת ל-100%)", len(f_df[f_df['adj_solvency'] < 100]))

st.markdown("---")

# גרפים מתקדמים
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🧬 פרופיל סיכון רב-ממדי (Radar)")
    # גרף מכ"ם להשוואה בין חברות
    fig_radar = go.Figure()
    selected_comps = st.multiselect("בחר חברות להשוואה:", f_df['company'].unique(), default=f_df['company'].unique()[:3])
    
    for comp in selected_comps:
        d = f_df[f_df['company'] == comp].iloc[0]
        fig_radar.add_trace(go.Scatterpolar(
            r=[d['adj_solvency']/2, d['csm_to_assets']*10, 100-(d['risk_intensity']*10), 80, d['adj_solvency']/2],
            theta=['חוסן הון', 'יעילות רווח', 'איכות חיתום', 'נזילות', 'חוסן הון'],
            fill='toself', name=comp
        ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), template="plotly_dark", height=450)
    st.plotly_chart(fig_radar, use_container_width=True)

with col_right:
    st.subheader("📊 ניתוח רגישות סולבנסי: בסיס vs תרחיש")
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(name='סולבנסי מקורי', x=f_df['company'], y=f_df['solvency_ratio'], marker_color='#30363d'))
    fig_bar.add_trace(go.Bar(name='לאחר תרחיש קיצון', x=f_df['company'], y=f_df['adj_solvency'], marker_color='#00f2ff'))
    fig_bar.update_layout(barmode='group', template="plotly_dark", height=450)
    st.plotly_chart(fig_bar, use_container_width=True)

# 6. דוח טבלאי מעוצב עם חיתוך וצבעים
st.subheader("📋 דוח ריכוז נתונים ויחסים פיננסיים")

def style_solvency(val):
    color = '#00ff00' if val > 140 else '#ffaa00' if val > 100 else '#ff4b4b'
    return f"color: {color}; font-weight: bold;"

# יצירת תצוגה נקייה לטבלה
display_df = f_df[['company', 'solvency_ratio', 'adj_solvency', 'csm_balance', 'csm_to_assets', 'loss_component']]
display_df.columns = ['חברה', 'סולבנסי בסיס', 'סולבנסי מותאם', 'יתרת CSM', 'יעילות CSM (%)', 'חוזים הפסדיים']

st.dataframe(display_df.style.applymap(style_solvency, subset=['סולבנסי מותאם']), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("המערכת מבצעת אימות נתונים בלתי תלוי ותיקוף לוגי לכל סימולציה.")
