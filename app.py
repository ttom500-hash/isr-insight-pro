import streamlit as st
import os

st.set_page_config(page_title="בדיקת כספת", direction="rtl")
st.title("🔍 בדיקת כספת (Secrets Debugger)")

st.write("בודק מה המערכת רואה בתוך ה-Secrets...")

# בדיקה 1: האם הכספת קיימת בכלל?
if not st.secrets:
    st.error("❌ הכספת ריקה לחלוטין! (st.secrets is empty)")
    st.warning("המשמעות: שום דבר לא נשמר בהגדרות, או שאתה באפליקציה הלא נכונה.")
else:
    st.success("✅ הכספת לא ריקה! הנה מה שמצאתי בפנים:")
    
    # בדיקה 2: הדפסת שמות המפתחות (בלי לחשוף את הסיסמה עצמה)
    found_key = False
    for key in st.secrets:
        st.markdown(f"🔑 מצאתי מפתח בשם: `{key}`")
        
        if key == "GOOGLE_API_KEY":
            found_key = True
            value = st.secrets[key]
            st.info(f"👍 המפתח `GOOGLE_API_KEY` קיים!")
            st.write(f"אורך המפתח: {len(value)} תווים")
            st.write(f"התחלה: `{value[:5]}...`")
            st.write(f"סוף: `...{value[-5:]}`")
            
            if " " in value:
                st.error("⚠️ אזהרה: יש רווחים בתוך המפתח! זה לא תקין.")
            if value.startswith('"') or value.endswith('"'):
                st.error("⚠️ אזהרה: המפתח מכיל מרכאות מיותרות כחלק מהטקסט.")

    if not found_key:
        st.error("❌ לא מצאתי מפתח בשם `GOOGLE_API_KEY`.")
        st.info("טיפ: אולי שמרת אותו בשם אחר? (למשל google_api_key באותיות קטנות?)")
