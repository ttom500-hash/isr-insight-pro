import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="בדיקת מפתח", direction="rtl")
st.title("🔑 בדיקת חיבור לגוגל")

# 1. בדיקת המפתח
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    st.success(f"המפתח נקלט (מתחיל ב: {api_key[:5]}...)")
else:
    st.error("חסר מפתח ב-Secrets")
    st.stop()

# 2. ניסיון קבלת רשימת מודלים
st.write("מנסה ליצור קשר עם השרתים של גוגל...")

try:
    models = list(genai.list_models())
    st.write("### ✅ הצלחנו! הנה המודלים הזמינים למפתח שלך:")
    
    found_any = False
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            st.code(m.name) # מציג את השם המדויק
            found_any = True
            
    if not found_any:
        st.warning("החיבור הצליח, אבל לא נמצאו מודלים לטקסט (מוזר!)")
        
except Exception as e:
    st.error("❌ החיבור נכשל.")
    st.error(f"השגיאה המדויקת: {e}")
    st.info("סיבות אפשריות: המפתח חסום, או שגוגל חסמו את ה-IP הזה זמנית.")
