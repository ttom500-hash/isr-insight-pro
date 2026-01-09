import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="X-RAY Debug", layout="wide")
st.title("X-RAY Debugger 🩻")

# 1. שליפת המפתח (תומך בשני השמות)
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ לא נמצא שום מפתח ב-Secrets!")
    st.stop()

st.write(f"מפתח נמצא (מתחיל ב-{api_key[:5]})... מנסה להתחבר...")

# 2. הגדרת המפתח
genai.configure(api_key=api_key)

# 3. ניסיון ישיר ללא שום הגנות (כדי לראות את השגיאה המקורית)
st.write("מנסה לשלוח 'Hello' למודל gemini-1.5-flash...")

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Hello")
    st.success(f"🎉 הצלחנו! התשובה: {response.text}")
    
except Exception as e:
    st.error("💥 התקבלה שגיאה מגוגל:")
    # הדפסת השגיאה בתוך תיבת קוד כדי שיהיה קל לקרוא
    st.code(str(e), language="text")
    
    st.write("---")
    st.write("מנסה גם את gemini-pro הישן...")
    try:
        model_old = genai.GenerativeModel("gemini-pro")
        response_old = model_old.generate_content("Hello")
        st.success(f"🎉 הישן עובד! {response_old.text}")
    except Exception as e2:
         st.code(str(e2), language="text")
