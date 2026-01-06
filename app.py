import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# הגדרות דף למראה מקצועי
st.set_page_config(page_title="ISR-Insight Pro | פיקוח ביטוח", layout="wide")

# עיצוב מותאם אישית (CSS) למראה "מהפנט"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { color: #00d4ff; font-size: 32px; }
    .stSelectbox label { color: white; font-weight: bold; }
    h1, h2, h3 { color: #ffffff; font-family: 'Segoe UI', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# פונקציה לטעינת הנתונים מהמחסן שיצרנו
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/database.csv')
        return df
    except:
        st.error("לא נמצא קובץ נתונים. וודא שתיקיית data קיימת.")
        return pd.DataFrame()

df = load_data()

# כותרת ראשית
st.title("🛡️ מערכת פיקוח דינמית: IFRS 17 & Solvency II")
st.markdown("---")

if not df.empty:
    # סרגל צד לבחירת חברה
    st.sidebar.header("אפשרויות פיקוח")
    selected_company = st.sidebar.selectbox("בחר חברת ביטוח לניתוח מעמיק:", df['company'].unique())
    
    # סינון נתונים לחברה הנבחרת
    c_data = df[df['company'] == selected_company].iloc[0]

    # שורת מדדים עליונה (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("יחס סולבנסי", f"{c_data['solvency_ratio']}%", "2%+")
    with col2:
        st.metric("יתרת CSM (מיליארד ₪)", f"{c_data['csm_balance']}", "0.4+")
    with col3:
        st.metric("Loss Component (מיליון ₪)", f"{c_data['loss_component']}", "-15", delta_color="inverse")
    with col4:
        status = "🟢 תקין" if c_data['solvency_ratio'] > 150 else "🟡 במעקב"
        st.metric("סטטוס רגולטורי", status)

    st.markdown("### ניתוח ויזואלי השוואתי")
    
    tab1, tab2 = st.tabs(["📊 השוואת ענף", "📈 מגמות חברה"])
    
    with tab1:
        # גרף בועות - חוסן הון מול רווחיות עתידית
        fig = px.scatter(df, x="solvency_ratio", y="csm_balance", size="loss_component", 
                         color="company", hover_name="company",
                         labels={"solvency_ratio": "יחס סולבנסי (%)", "csm_balance": "יתרת CSM (רווח עתידי)"},
                         title="מפת סיכון: חוסן הון (X) מול פוטנציאל רווח (Y)")
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            # מד מהירות ליחס סולבנסי
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = c_data['solvency_ratio'],
                title = {'text': f"מדד יציבות - {selected_company}"},
                gauge = {
                    'axis': {'range': [None, 200]},
                    'bar': {'color': "#00d4ff"},
                    'steps': [
                        {'range': [0, 100], 'color': "red"},
                        {'range': [100, 140], 'color': "orange"},
                        {'range': [140, 200], 'color': "green"}]
                }
            ))
            fig_gauge.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
        with col_b:
            # גרף עמודות ל-Loss Component
            fig_bar = px.bar(df, x='company', y='loss_component', color='company',
                             title="חוזים הפסדיים (Loss Component) - השוואת ענף")
            fig_bar.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.warning("ממתין לנתונים ראשוניים מהסורק...")

st.sidebar.markdown("---")
st.sidebar.info("המערכת סורקת נתונים מאתר מאיה ומדוחות כספיים (PDF) באופן אוטומטי.")
