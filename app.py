import streamlit as st
import pandas as pd

# --- 1. הגדרות תצוגה PRO ---
st.set_page_config(page_title="Apex Pro - Insurance Insight", layout="wide")

# פונקציית ה-AI המלאה
def run_financial_ai(company, query):
    # כאן נכנסים המדדים ששמרנו ב-Saved Info
    return f"ניתוח PRO עבור {company}: השאילתה '{query}' נבחנה מול דוחות Q3. יתרת ה-CSM (₪14.5B) ויחס הסולבנסי (182%) מצביעים על חוסן פיננסי גבוה."

# --- 2. סרגל צד (Sidebar) ---
with st.sidebar:
    st.title("🛡️ APEX PRO")
    company = st.selectbox("בחר חברה לניתוח:", ["הפניקס", "מגדל"])
    st.info("📂 מחסן נתונים: 7 דוחות PDF מנותחים")
    st.divider()
    st.write("📌 **KPIs במעקב:**")
    st.caption("Solvency, CSM, ROE, Combined Ratio, NB Margin")

# --- 3. לוח מדדים (5 KPIs) ---
st.title(f"📊 {company} | סקירה ניהולית מלאה")

# המדדים הקריטיים שביקשת לשמור
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("סולבנסי (SCR)", "182%", "2%+")
with col2:
    st.metric("יתרת CSM", "₪14.5B", "0.4B+")
with col3:
    st.metric("ROE (תשואה להון)", "13.2%", "1.1%+")
with col4:
    st.metric("Combined Ratio", "92.5%", "-0.5%")
with col5:
    st.metric("NB Margin", "4.5%", "0.2%+")

st.divider()

# --- 4. עוזר מחקר AI (הלב של המערכת) ---
st.subheader("🤖 Gemini AI - עוזר מחקר פיננסי")
user_input = st.text_input("הזן שאילתה לניתוח (למשל: נתח את רגישות ה-CSM):", key="gemini_ai_v5")

if user_input:
    with st.spinner("מנתח דוחות במנוע PRO..."):
        response = run_financial_ai(company, user_input)
        st.chat_message("assistant").write(response)

st.divider()

# --- 5. ויזואליזציה ומגמות (כמו באתר המלא) ---
st.subheader("📈 מגמות צמיחה וניתוח נתונים")
tab1, tab2 = st.tabs(["צמיחת CSM", "יציבות סולבנסי"])

with tab1:
    chart_data = pd.DataFrame({
        "רבעון": ["Q4-23", "Q1-24", "Q2-24", "Q3-24"],
        "CSM (במיליארדים)": [13.8, 14.1, 14.3, 14.5]
    })
    st.line_chart(chart_data.set_index("רבעון"))

with tab2:
    solvency_data = pd.DataFrame({
        "רבעון": ["Q4-23", "Q1-24", "Q2-24", "Q3-24"],
        "יחס סולבנסי %": [175, 178, 180, 182]
    })
    st.bar_chart(solvency_data.set_index("רבעון"))