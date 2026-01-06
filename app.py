import streamlit as st
import pandas as pd
import plotly.express as px

# 1. הגדרת עמוד (RTL)
st.set_page_config(page_title="ISR-INSIGHT PRO", layout="wide", page_icon="🛡️")
st.markdown("""
    <style>
    body {direction: rtl;}
    .stApp {direction: rtl; text-align: right;}
    div[data-testid="stMetricValue"] {text-align: right; direction: ltr;}
    div[data-testid="stMarkdownContainer"] p {text-align: right;}
    h1, h2, h3, h4, h5, h6 {text-align: right;}
    .css-10trblm {text-align: right;}
    div[data-testid="stDataFrame"] {direction: rtl;}
    </style>
    """, unsafe_allow_html=True)

# 2. כותרת ראשית
st.title("🛡️ ISR-INSIGHT PRO | מערכת פיקוח ענפית")
st.markdown("### דשבורד ניתוח IFRS 17 - תמונת מצב עדכנית (2025/26)")

# 3. מאגר הנתונים המלא (הפניקס, הראל, מנורה, כלל, מגדל, איילון, הכשרה, ישיר, ווישור, ליברה)
data = [
    {"חברה": "הפניקס", "סוג": "5 הגדולות", "CSM (M₪)": 8200, "ROE (%)": 19.2, "סולבנסי (%)": 188, "רווח נקי": 1745, "סיכון": "בינוני"},
    {"חברה": "הראל", "סוג": "5 הגדולות", "CSM (M₪)": 9100, "ROE (%)": 16.0, "סולבנסי (%)": 195, "רווח נקי": 1152, "סיכון": "נמוך"},
    {"חברה": "מנורה מבטחים", "סוג": "5 הגדולות", "CSM (M₪)": 7400, "ROE (%)": 16.8, "סולבנסי (%)": 182, "רווח נקי": 985, "סיכון": "נמוך"},
    {"חברה": "כלל ביטוח", "סוג": "5 הגדולות", "CSM (M₪)": 6800, "ROE (%)": 11.2, "סולבנסי (%)": 162, "רווח נקי": 742, "סיכון": "בינוני-גבוה"},
    {"חברה": "מגדל", "סוג": "5 הגדולות", "CSM (M₪)": 7100, "ROE (%)": 9.4, "סולבנסי (%)": 158, "רווח נקי": 610, "סיכון": "גבוה"},
    {"חברה": "ביטוח ישיר", "סוג": "דיגיטלי/ישיר", "CSM (M₪)": 1200, "ROE (%)": 25.5, "סולבנסי (%)": 165, "רווח נקי": 280, "סיכון": "בינוני"},
    {"חברה": "איילון", "סוג": "בינוני", "CSM (M₪)": 950, "ROE (%)": 17.2, "סולבנסי (%)": 148, "רווח נקי": 320, "סיכון": "גבוה"},
    {"חברה": "הכשרה", "סוג": "בינוני", "CSM (M₪)": 450, "ROE (%)": 24.0, "סולבנסי (%)": 113, "רווח נקי": 68, "סיכון": "גבוה מאוד"},
    {"חברה": "WeSure", "סוג": "דיגיטלי/ישיר", "CSM (M₪)": 180, "ROE (%)": 44.5, "סולבנסי (%)": 160, "רווח נקי": 188, "סיכון": "בינוני"},
    {"חברה": "ליברה", "סוג": "דיגיטלי/ישיר", "CSM (M₪)": 140, "ROE (%)": 22.0, "סולבנסי (%)": 155, "רווח נקי": 55, "סיכון": "גבוה"}
]
df = pd.DataFrame(data)

# 4. לשוניות ניווט
tab1, tab2, tab3 = st.tabs(["📊 מבט על", "🔎 צלילת עומק", "⚡ סימולטור סיכונים"])

with tab1:
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("סך CSM ענפי", f"₪{df['CSM (M₪)'].sum():,.0f}M")
    col2.metric("ROE ממוצע (משוקלל)", f"{df['ROE (%)'].mean():.1f}%")
    col3.metric("חברות מתחת ל-160% סולבנסי", len(df[df['סולבנסי (%)'] < 160]))
    col4.metric("החברה הרווחית ביותר (ROE)", df.loc[df['ROE (%)'].idxmax()]['חברה'])
    
    st.divider()
    
    # Main Charts
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("דירוג יציבות הון (Solvency)")
        fig_sol = px.bar(df.sort_values('סולבנסי (%)'), x="חברה", y="סולבנסי (%)", color="סיכון",
                         color_discrete_map={"נמוך": "green", "בינוני": "yellow", "גבוה": "orange", "גבוה מאוד": "red"},
                         text="סולבנסי (%)")
        st.plotly_chart(fig_sol, use_container_width=True)
    
    with c2:
        st.subheader("מלאי רווח עתידי (CSM) מול יעילות הון")
        fig_scat = px.scatter(df, x="CSM (M₪)", y="ROE (%)", size="רווח נקי", color="סוג", hover_name="חברה",
                              text="חברה", size_max=60)
        st.plotly_chart(fig_scat, use_container_width=True)

with tab2:
    st.subheader("טבלת נתונים מלאה - IFRS 17")
    
    # פילטרים
    selected_types = st.multiselect("סנן לפי סוג חברה:", df["סוג"].unique(), default=df["סוג"].unique())
    df_filtered = df[df["סוג"].isin(selected_types)]
    
    # עיצוב מותנה לטבלה
    def highlight_risk(val):
        if val < 150: return 'background-color: #ffcccc; color: black' # אדום בהיר
        if val > 180: return 'background-color: #ccffcc; color: black' # ירוק בהיר
        return ''

    st.dataframe(
        df_filtered.style.applymap(highlight_risk, subset=['סולבנסי (%)'])
                   .format({"CSM (M₪)": "{:,.0f}", "רווח נקי": "{:,.0f}", "ROE (%)": "{:.1f}%", "סולבנסי (%)": "{:.0f}%"}),
        use_container_width=True,
        height=500
    )

with tab3:
    st.subheader("מחשבון השפעת שוק (Stress Test Simulator)")
    st.info("הזז את הסליידרים כדי לראות כיצד שינויי מאקרו ישפיעו על ה-CSM הענפי")
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        interest_change = st.slider("שינוי בריבית (אחוזים)", -2.0, 2.0, 0.0, 0.1)
    with col_sim2:
        market_crash = st.slider("ירידה בשוק המניות (אחוזים)", -20, 0, 0, 1)
        
    # לוגיקה פשוטה להדגמה
    impact_factor = 1 + (interest_change * 0.05) + (market_crash * 0.02)
    new_total_csm = df['CSM (M₪)'].sum() * impact_factor
    loss = df['CSM (M₪)'].sum() - new_total_csm
    
    st.metric("סך CSM חזוי לאחר זעזוע", f"₪{new_total_csm:,.0f}M", f"{loss:,.0f}M-", delta_color="inverse")
    
    if loss > 5000:
        st.error("⚠️ התראה: תרחיש זה יוביל לפגיעה מהותית ביציבות הענף!")
    elif loss > 0:
        st.warning("שים לב: שחיקה ברווחיות העתידית.")
    else:
        st.success("התרחיש חיובי לענף.")
