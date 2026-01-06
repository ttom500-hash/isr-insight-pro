import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. הגדרות UI - עיצוב "חדר מלחמה" רגולטורי
st.set_page_config(page_title="ISR-Insight Pro | חדר בקרה", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; direction: rtl; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 12px; border-left: 5px solid #00f2ff; }
    [data-testid="stMetricValue"] { color: #00f2ff; font-family: 'Segoe UI'; font-weight: bold; }
    .report-box { background-color: #1c2128; padding: 25px; border-radius: 12px; border: 1px solid #3b82f6; line-height: 1.6; }
    h1, h2, h3 { color: #00f2ff; text-align: right; }
    .stTabs [data-baseweb="tab"] { color: #8b949e; font-size: 20px; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom-color: #00f2ff !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. פונקציות לוגיקה
def get_recommendations(row):
    status = ""
    steps = []
    if row['adj_solvency'] < 110:
        status = f"חברת {row['company']} נמצאת בחריגה הונית חמורה בתרחיש הנבחר."
        steps = ["דרישה מיידית לתוכנית הון", "עצירת חלוקת דיבידנד", "הגברת פיקוח הדוק"]
    elif row['adj_solvency'] < 140:
        status = f"חברת {row['company']} מציגה חוסן גבולי. נדרש ניטור סיכוני שוק."
        steps = ["בחינת רכש ביטוח משנה", "הגבלת צמיחה בקווי עסקים מסוימים"]
    else:
        status = f"חברת {row['company']} שומרת על יציבות גבוהה וחוסן תפעולי."
        steps = ["המשך פיקוח שוטף", "אישור מדיניות דיבידנד שמרנית"]
    return status, steps

@st.cache_data
def load_data():
    try:
        return pd.read_csv('data/database.csv')
    except:
        return pd.DataFrame()

# 3. טעינה ועיבוד
df = load_data()
if df.empty:
    st.error("לא נמצאו נתונים. וודא שקובץ data/database.csv תקין.")
    st.stop()

# סרגל צד
st.sidebar.title("🧪 סימולטור תרחישים")
year_f = st.sidebar.selectbox("שנה", sorted(df['year'].unique(), reverse=True))
q_f = st.sidebar.selectbox("רבעון", df[df['year']==year_f]['quarter'].unique())
st.sidebar.markdown("---")
s_int = st.sidebar.slider("זעזוע ריבית (%)", -2.5, 2.5, 0.0, 0.1)
s_mkt = st.sidebar.slider("קריסת בורסה (%)", 0, 40, 0)
s_lapse = st.sidebar.slider("עליית ביטולים (%)", 0, 25, 0)
s_quake = st.sidebar.toggle("🚨 תרחיש רעידת אדמה (PML)")

# חישובי תרחיש
f_df = df[(df['year'] == year_f) & (df['quarter'] == q_f)].copy()
for i, row in f_df.iterrows():
    impact = (s_int * row['int_sensitivity'] * 100) - (s_mkt/10 * row['mkt_sensitivity'] * 100) - (s_lapse/5 * row['lapse_sensitivity'] * 100)
    if s_quake: impact -= 25
    f_df.at[i, 'adj_solvency'] = row['solvency_ratio'] + impact
    f_df.at[i, 'eff'] = (row['csm_balance'] / row['total_assets']) * 100
    f_df.at[i, 'quality'] = 100 - (row['loss_component'] / (row['csm_balance'] * 10))

# 4. תצוגה
st.title(f"🛡️ חדר בקרה רגולטורי - {q_f} {year_f}")
st.markdown("---")

# מדדים ענפיים
c1, c2, c3, c4 = st.columns(4)
c1.metric("ממוצע סולבנסי ענפי", f"{f_df['adj_solvency'].mean():.1f}%")
c2.metric("סך CSM (מיליארד)", f"{f_df['csm_balance'].sum():.1f}B")
c3.metric("חברות מתחת ל-110%", len(f_df[f_df['adj_solvency'] < 110]))
c4.metric("יעילות CSM ממוצעת", f"{f_df['eff'].mean():.1f}%")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📉 מפת שוק", "📊 סרגלי בריאות", "📝 דוח מנהלים"])

with tab1:
    st.subheader("חוסן הון (סולבנסי) מול יעילות רווח (CSM)")
    fig = px.scatter(f_df, x="adj_solvency", y="eff", size="total_assets", color="company", text="company",
                     labels={"adj_solvency": "חוסן הון %", "eff": "יעילות רווח %"})
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)



with tab2:
    st.subheader("השוואה ליניארית של כל חברות הענף")
    # הצגת סרגלי בריאות לכל החברות
    fig_h = go.Figure()
    for _, r in f_df.sort_values('adj_solvency', ascending=True).iterrows():
        color = '#00ff00' if r['adj_solvency'] > 140 else '#ffaa00' if r['adj_solvency'] > 110 else '#ff4b4b'
        fig_h.add_trace(go.Bar(y=[r['company']], x=[r['adj_solvency']/2], name='חוסן הון', orientation='h', marker_color=color))
        fig_h.add_trace(go.Bar(y=[r['company']], x=[r['eff']*5], name='יעילות רווח', orientation='h', marker_color='#00d4ff'))
        fig_h.add_trace(go.Bar(y=[r['company']], x=[r['quality']], name='איכות תיק', orientation='h', marker_color='#9b59b6'))

    fig_h.update_layout(barmode='group', template="plotly_dark", height=800, xaxis=dict(range=[0,100], title="ציון משוקלל"))
    st.plotly_chart(fig_h, use_container_width=True)

with tab3:
    st.subheader("סיכום הערכת פיקוח")
    audit_comp = st.selectbox("בחר חברה לניתוח עומק:", f_df['company'].unique())
    row_data = f_df[f_df['company'] == audit_comp].iloc[0]
    status, recs = get_recommendations(row_data)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(f"<div class='report-box'><b>הערכת מצב רגולטורית:</b><br><br>{status}</div>", unsafe_allow_html=True)
    with col_r:
        st.markdown("<b>צעדים מומלצים לפיקוח:</b>", unsafe_allow_html=True)
        for rc in recs: st.write(f"🔹 {rc}")

    st.markdown("---")
    st.write("📋 **נתוני גלם לאחר זעזוע:**")
    st.dataframe(f_df[['company', 'solvency_ratio', 'adj_solvency', 'csm_balance', 'loss_component']].style.format(precision=1), use_container_width=True)
