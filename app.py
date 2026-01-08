import streamlit as st

# הגדרות PRO - תצוגה ניהולית רחבה
st.set_page_config(page_title="Apex Pro - Insurance Insight", layout="wide")

# מנוע AI סימולטיבי יציב
def run_pro_analysis(company, query):
    return f"ניתוח PRO עבור {company}: השאילתה '{query}' נבחנה. יתרת ה-CSM (14.5B) ויחס הסולבנסי (182%) יציבים."

# --- סרגל כלים (Sidebar) ---
with st.sidebar:
    st.title("🛡️ APEX PRO")
    company = st.selectbox("בחר חברה:", ["הפניקס", "מגדל"])
    st.info("📂 מחסן נתונים: 7 דוחות PDF")
    st.button("רענן מערכת", key="final_refresh_btn")

# --- לוח בקרה (Dashboard) ---
st.title(f"📊 {company} | סקירה ניהולית")

col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("סולבנסי (SCR)", "182%")
with col2: st.metric("יתרת CSM", "₪14.5B")
with col3: st.metric("ROE", "13.2%")
with col4: st.metric("Combined", "92.5%")
with col5: st.metric("NB Margin", "4.5%")

st.divider()

# --- פיצ'ר AI יציב (שימוש ב-text_input למניעת Freeze) ---
st.subheader("🤖 Gemini AI - עוזר מחקר")
user_input = st.text_input("הזן שאילתה לניתוח:", key="ai_input_v3")

if user_input:
    try:
        with st.spinner("מנתח..."):
            res = run_pro_analysis(company, user_input)
            st.info(res)
    except Exception as e:
        st.error(f"שגיאה: {e}")

# --- גרפים סגורים הרמטית (תיקון שורות 41-44) ---
t1, t2 = st.tabs(["צמיחת CSM", "סולבנסי"])
with t1: st.line_chart([13.8, 14.1, 14.3, 14.5])
with t2: st.bar_chart([175, 178, 180, 182])