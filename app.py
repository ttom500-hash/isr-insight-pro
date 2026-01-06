import streamlit as st
import pandas as pd
import plotly.express as px

# 1. הגדרת עמוד ותצורה (RTL לעברית)
st.set_page_config(page_title="ISR-INSIGHT PRO", layout="wide", page_icon="🛡️")

# הזרקת CSS כדי שהאפליקציה תהיה מימין לשמאל (RTL)
st.markdown("""
    <style>
    body {direction: rtl;}
    .stApp {direction: rtl; text-align: right;}
    div[data-testid="stMetricValue"] {text-align: right;}
    p, h1, h2, h3 {text-align: right;}
    </style>
    """, unsafe_allow_html=True)

# 2. כותרת ראשית
st.title("🛡️ ISR-INSIGHT PRO | דשבורד פיקוח ביטוח")
st.markdown("### מערכת ניתוח ובקרה למבטחים (IFRS 17)")

# 3. נתונים מדומים (הדמיה של מה שה-AI חילץ)
# בהמשך נחבר את זה למנוע ה-PDF
data = {
    "חברה": ["הפניקס", "הראל", "מנורה מבטחים", "ביטוח ישיר", "איילון", "מגדל"],
    "רווח נקי (M₪)": [1745, 1152, 985, 280, 320, 610],
    "CSM (M₪)": [8200, 9100, 7400, 1200, 950, 7100],
    "ROE (%)": [19.2, 16.0, 16.8, 25.5, 17.2, 9.4],
    "יחס סולבנסי (%)": [188, 195, 182, 165, 148, 158],
    "סטטוס רגולטורי": ["תקין", "תקין", "תקין", "מעקב", "אזהרה", "תקין"]
}
df = pd.DataFrame(data)

# 4. סרגל צד (Sidebar)
st.sidebar.header("⚙️ הגדרות מערכת")
selected_companies = st.sidebar.multiselect(
    "בחר חברות להשוואה:",
    options=df["חברה"].unique(),
    default=["הפניקס", "הראל", "מנורה מבטחים"]
)

# סינון הנתונים לפי הבחירה
df_filtered = df[df["חברה"].isin(selected_companies)]

# 5. מדדי על (KPIs)
col1, col2, col3, col4 = st.columns(4)
col1.metric("ממוצע ROE ענפי", f"{df_filtered['ROE (%)'].mean():.1f}%", "1.2%+")
col2.metric("סה\"כ CSM נבחר", f"₪{df_filtered['CSM (M₪)'].sum():,.0f}M")
col3.metric("חברות בסיכון", len(df_filtered[df_filtered['סטטוס רגולטורי'] == 'אזהרה']), "נמוך")
col4.metric("יחס סולבנסי ממוצע", f"{df_filtered['יחס סולבנסי (%)'].mean():.0f}%")

st.divider()

# 6. גרפים ויזואליים
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 השוואת יעילות הון (ROE)")
    fig_roe = px.bar(df_filtered, x="חברה", y="ROE (%)", color="חברה", text="ROE (%)",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_roe, use_container_width=True)

with c2:
    st.subheader("💰 מלאי רווח עתידי (CSM)")
    fig_csm = px.pie(df_filtered, values='CSM (M₪)', names='חברה', hole=0.4)
    st.plotly_chart(fig_csm, use_container_width=True)

# 7. טבלת נתונים חכמה עם סימון חריגות
st.subheader("📋 נתוני עומק וסטטוס פיקוחי")

def highlight_solvency(val):
    color = 'red' if val < 150 else 'green'
    return f'color: {color}; font-weight: bold;'

st.dataframe(
    df_filtered.style.applymap(highlight_solvency, subset=['יחס סולבנסי (%)']),
    use_container_width=True
)

# 8. אזור AI (סימולציה)
st.info("🤖 **תובנת AI:** זוהתה חריגה חיובית בתשואה על ההון של 'ביטוח ישיר' הנובעת מהתייעלות תפעולית. מנגד, 'איילון' מתקרבת לגבול הסולבנסי התחתון.")
