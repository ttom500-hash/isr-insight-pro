import streamlit as st
import google.generativeai as genai
import os

# --- 1. הגדרות דף ---
st.set_page_config(page_title="Apex Insurance Intelligence Pro", layout="wide")

# --- 2. חיבור מתוקן ל-AI ---
def init_ai():
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # שימוש במודל בגרסה המפורשת למניעת שגיאת 404
        return genai.GenerativeModel('models/gemini-1.5-flash')
    return None

model = init_ai()

# --- 3. עיצוב (Ticker Tape) ---
st.markdown('<div style="background-color: #1c2e4a; color: white; padding: 10px; text-align: center; font-weight: bold;">📊 מערכת פיקוח הוליסטית - ניתוח דוחות כספיים</div>', unsafe_allow_html=True)

# --- 4. סרגל ניווט ---
with st.sidebar:
    st.title("🏛️ ניהול פיקוח")
    company = st.selectbox("חברה מדווחת", ["Harel"])
    year = st.selectbox("שנת דיווח", ["2025"])
    quarter = st.radio("רבעון", ["Q1"])
    st.divider()
    
    fin_file = f"data/{company}/{year}/{quarter}/financial/financial_report.pdf"
    
    if model:
        st.success("מנוע AI מחובר ✅")
    else:
        st.error("חסר API Key ב-Secrets! ❌")

# --- 5. גוף המערכת ---
st.title(f"ניתוח הוליסטי: {company} - {quarter}/{year}")

tab1, tab2 = st.tabs(["📊 IFRS 17 & רווחיות", "🛡️ יציבות (Solvency II)"])

with tab1:
    st.subheader("ניתוח נתוני רווחיות ו-CSM")
    
    if os.path.exists(fin_file):
        st.success(f"קובץ זוהה: financial_report.pdf")
        
        if st.button("🚀 הפעל ניתוח AI עמוק"):
            with st.spinner("מנתח את הדוח... אנא המתן"):
                try:
                    # טעינת הקובץ
                    with open(fin_file, "rb") as f:
                        pdf_data = f.read()
                    
                    # הכנת התוכן לשליחה בפורמט התואם לגרסה החדשה
                    content_parts = [
                        {"mime_type": "application/pdf", "data": pdf_data},
                        "Extract: Net Profit, Total CSM, ROE, and Gross Premiums for Harel Q1 2025. Hebrew results."
                    ]
                    
                    # הפעלת המודל
                    response = model.generate_content(content_parts)
                    
                    st.markdown("### 🔍 ממצאי ה-AI:")
                    st.write(response.text)
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"שגיאה בניתוח: {str(e)}")
                    st.info("מנסה שיטה חלופית...")
    else:
        st.warning(f"קובץ לא נמצא בנתיב: {fin_file}")
