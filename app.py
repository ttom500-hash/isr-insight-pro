import streamlit as st
import google.generativeai as genai
import os

# --- 1. הגדרת דף (תיקון: ללא הפרמטר השגוי) ---
st.set_page_config(page_title="בדיקת מפתח", layout="wide")

# --- 2. עיצוב RTL (כאן זה המקום הנכון) ---
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
</style>
""", unsafe_allow_html=True)

st.title("🔑 בדיקת חיבור לגוגל")

# --- 3. בדיקת המפתח ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    st.success(f"המפתח ב-Secrets זוהה (מתחיל ב: {api_key[:5]}...)")
else:
    st.error("❌ חסר מפתח ב-Secrets. נא להוסיף אותו.")
    st.stop()

# --- 4. בדיקת חיבור למודלים ---
st.info("מנסה ליצור קשר עם גוגל...")

try:
    # בקשת רשימת המודלים הפתוחים
    models = list(genai.list_models())
    
    found_flash = False
    found_pro = False
    
    st.write("### 📋 תוצאות הבדיקה:")
    
    for m in models:
        # בדיקה אם המודל תומך ביצירת תוכן
        if 'generateContent' in m.supported_generation_methods:
            st.write(f"- זמין: `{m.name}`")
            if "flash" in m.name: found_flash = True
            if "pro" in m.name: found_pro = True
            
    if found_flash or found_pro:
        st.success("✅ יש אישור! המפתח תקין והמודלים זמינים.")
        st.balloons()
    else:
        st.warning("⚠️ החיבור הצליח, אבל לא נמצאו מודלים חדשים (Flash/Pro).")
        
except Exception as e:
    st.error("❌ החיבור נכשל לחלוטין.")
    st.error(f"שגיאה: {e}")
    st.markdown("**המשמעות:** המפתח הזה חסום או לא תקין. עליך ליצור מפתח חדש ב-Google AI Studio.")
