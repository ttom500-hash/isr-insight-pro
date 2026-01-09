import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="Key Diagnostics", layout="centered")

st.title("🔧 בדיקת מפתח API")

# 1. שליפת המפתח
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ חסר מפתח API ב-Secrets")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"].strip()
st.write(f"🔑 מפתח מזוהה (מתחיל ב): `{api_key[:5]}...`")

# 2. ניסיון התחברות
if st.button("בצע בדיקת תקשורת מול גוגל"):
    genai.configure(api_key=api_key)
    
    try:
        st.info("מתחבר לשרתי Google Generative AI...")
        
        # בקשה לרשימת המודלים הפתוחים למפתח הזה
        models = list(genai.list_models())
        
        found_any = False
        st.write("---")
        st.subheader("📋 תוצאות הסריקה:")
        
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                st.success(f"✅ מודל זמין: {m.name}")
                found_any = True
        
        if not found_any:
            st.error("❌ התקשורת הצליחה, אבל המפתח שלך לא רואה אף מודל צ'אט (generateContent).")
            st.warning("הסיבה: כנראה הפרויקט ב-Google Cloud חסום או לא מאופשר ל-Generative Language API.")
        else:
            st.balloons()
            st.success("✨ המפתח תקין לחלוטין! הבעיה הייתה בקוד הקודם.")

    except Exception as e:
        st.error(f"❌ שגיאה קריטית (המפתח לא עובד):")
        st.code(str(e))
        st.markdown("### 💡 הפתרון:")
        st.markdown("המפתח הזה 'מת'. גש ל-Google AI Studio והנפק מפתח חדש בפרויקט חדש.")
