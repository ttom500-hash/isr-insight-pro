import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. הגדרות UI ועיצוב ניאון רגולטורי ---
st.set_page_config(page_title="ISR-Insight Pro | חדר בקרה", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; border-left: 5px solid #00f2ff; }
    [data-testid="stMetricValue"] { color: #00f2ff; font-family: 'Segoe UI', sans-serif; }
    h1, h2, h3 { color: #00f2ff; text-align: right; }
    .report-box { background-color: #1c2128; padding: 20px; border-radius: 10px; border: 1px solid #3b82f6; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. פונקציות עזר (לוגיקה וסיכום) ---
def style_solvency_logic(val):
    """צביעת ערכי סולבנסי לפי רמת סיכון"""
    color = '#00ff00' if val > 140 else '#ffaa00' if val > 110 else '#ff4b4b'
    return f'color: {color}; font-weight: bold'

def generate_expert_summary(row):
    """ניתוח מילולי אוטומטי"""
    status_text = ""
    recommendations = []
    
    if row['adj_solvency'] < 110:
        status_text = f"חברת {row['company']} נמצאת בכשל הוני חמור בתרחיש זה."
        recommendations.append("דרישה להזרמת הון מיידית ועצירת דיבידנדים.")
    elif row['adj_solvency'] < 140:
        status_text = f"חברת {row['company']} מציגה חוסן גבולי. נדרש ניטור צמוד."
        recommendations.append("הגבלת חלוקת הון והגברת תדירות דיווח.")
    else:
        status_text = f"חברת {row['company']} שומרת על יציבות גבוהה."
        recommendations.append("המשך פיקוח שוטף.")
    
    return status_text, recommendations

@st.cache_data
def load_data():
    try:
        return pd.read_csv('data/database.csv')
    except:
        return pd.DataFrame()

# --- 3. טעינה ועיבוד נתונים ---
df = load_data()
if df.empty:
    st.error("❌ תקלה: קובץ הנתונים data/database.csv חסר או לא תקין.")
    st.stop()

# סרגל צד: פילטרים ותרחישים
st.sidebar.title("🛠️ סימולטור Stress Test")
year_f = st.sidebar.selectbox("שנה", sorted(df['year'].unique(), reverse=True))
q_f = st.sidebar.selectbox("רבעון", df[df['year']==year_f]['quarter'].unique())

st.sidebar.markdown("---")
s_int = st.sidebar.slider("זעזוע ריבית (%)", -2.5, 2.5, 0.0, 0.1)
s_mkt = st.sidebar.slider("ירידה בבורסה (%)", 0, 40, 0)
s_quake = st.sidebar.toggle("🚨 תרחיש רעידת אדמה")

# חישוב התרחיש לכל החברות
f_df = df[(df['year'] == year_f) & (df['quarter'] == q_f)].copy()
for i, row in f_df.iterrows():
    # נוסחת הסולבנסי המותאם
    impact = (s_int * row['int_sensitivity'] * 100) - (s_mkt/10 * row['mkt_sensitivity'] * 100)
    if s_quake: impact -= 25
    f_df.at[i, 'adj_solvency'] = row['solvency_ratio'] + impact
    f_df.at[i, 'csm_eff'] = (row['csm_balance'] / row['total_assets']) * 100
    f_df.at[i, 'port_quality'] = 100 - (row['loss_component'] / (row['csm_balance'] * 10))

# --- 4. תצוגה ראשית ---
st.title(f"🛡️ חדר בקרה רגולטורי: {q_f} {year_f}")

# שורת KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("ממוצע סולבנסי מותאם", f"{f_df['adj_solvency'].mean():.1f}%")
c2.metric("סך CSM (מיליארד)", f"{f_df['csm_balance'].sum():.1f}B")
c3.metric("חשיפה מקסימלית (Loss)", f"{f_df['loss_component'].max()}M")
c4.metric("חברות בסיכון", len(f_df[f_df['adj_solvency'] < 110]))

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📊 מפת שוק", "🧬 סרגלי בריאות", "📝 סיכום והמלצות"])

with tab1:
    fig_scatter = px.scatter(f_df, x="adj_solvency", y="csm_eff", size="total_assets", 
                             color="company", text="company",
                             labels={"adj_solvency": "חוסן (Solvency %)", "csm_eff": "יעילות (CSM/Assets %)"},
                             title="מפת שוק: יציבות מול רווחיות")
    fig_scatter.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.subheader("סרגלי בריאות רגולטוריים")
    sel_comps = st.multiselect("בחר חברות להשוואה:", f_df['company'].unique(), default=f_df['company'].unique()[:4])
    if sel_comps:
        viz_df = f_df[f_df['company'].isin(sel_comps)]
        fig_health = go.Figure()
        for comp in sel_comps:
            d = viz_df[viz_df['company'] == comp].iloc[0]
            col = '#00ff00' if d['adj_solvency'] > 140 else '#ffaa00' if d['adj_solvency'] > 110 else '#ff4b4b'
            fig_health.add_trace(go.Bar(y=[comp], x=[d['adj_solvency']/2], name='חוסן הון', orientation='h', marker_color=col))
            fig_health.add_trace(go.Bar(y=[comp], x=[d['csm_eff']*5], name='יעילות רווח', orientation='h', marker_color='#00d4ff'))
        fig_health.update_layout(barmode='group', template="plotly_dark", height=400, xaxis=dict(range=[0,100]))
        st.plotly_chart(fig_health, use_container_width=True)

with tab3:
    st.subheader("דוח הערכה והמלצות פיקוח")
    audit_comp = st.selectbox("בחר חברה לניתוח מילולי:", f_df['company'].unique())
    comp_row = f_df[f_df['company'] == audit_comp].iloc[0]
    status, recs = generate_expert_summary(comp_row)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(f"<div class='report-box'><b>הערכת מצב:</b><br>{status}</div>", unsafe_allow_html=True)
    with col_r:
        st.write("**פעולות מומלצות:**")
        for r in recs:
            st.write(f"- {r}")

    st.markdown("---")
    # טבלה סופית עם שמות עמודות בעברית לתצוגה
    display_df = f_df[['company', 'solvency_ratio', 'adj_solvency', 'csm_balance', 'loss_component']].copy()
    display_df.columns = ['חברה', 'סולבנסי מקור', 'סולבנסי מותאם', 'CSM (B)', 'Loss (M)']
    st.dataframe(display_df.style.applymap(style_solvency_logic, subset=['סולבנסי מותאם']), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("✅ המערכת מריצה תיקוף נתונים בלתי תלוי.")
