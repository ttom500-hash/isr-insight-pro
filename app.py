import streamlit as st
import requests

st.set_page_config(page_title="Apex Pro - Diagnostics", layout="wide")
st.title("🔍 אבחון עומק - תקשורת גוגל")

# 1. בדיקת קיום המפתח ב-Secrets
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ המפתח GOOGLE_API_KEY לא נמצא ב-Secrets של Streamlit!")
else:
    # הצגת 4 תווים אחרונים של המפתח לוודא שזה המפתח הנכון (בלי לחשוף אותו)
    st.info(f"✅ מפתח מזוהה (סיומת: {api_key[-4:]})")

    # 2. בדיקת רשימת המודלים שהמפתח הזה מורשה לגשת אליהם
    st.subheader("בדיקת הרשאות מפתח (List Models)")
    
    # ננסה גם v1 וגם v1beta
    endpoints = [
        "https://generativelanguage.googleapis.com/v1/models",
        "https://generativelanguage.googleapis.com/v1beta/models"
    ]
    
    for url in endpoints:
        st.write(f"בודק כתובת: `{url}`")
        try:
            res = requests.get(f"{url}?key={api_key}")
            if res.status_code == 200:
                models = res.json().get('models', [])
                model_names = [m['name'].split('/')[-1] for m in models]
                st.success(f"הצלחתי! מודלים זמינים בכתובת זו: {', '.join(model_names)}")
            else:
                st.error(f"שגיאה {res.status_code} בכתובת זו: {res.text}")
        except Exception as e:
            st.error(f"שגיאה טכנית: {str(e)}")

st.divider()
st.caption("Apex Insurance Intelligence | System Diagnostic Mode")
