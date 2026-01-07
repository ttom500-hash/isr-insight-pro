import streamlit as st
import pandas as pd
import os

# הגדרות דף
st.set_page_config(page_title="Insurance Pro", layout="wide")

st.title("🏛️ Insurance Insight Pro")

# בדיקה אם הקובץ קיים לפני הטעינה
file_path = 'data/database.csv'

if os.path.exists(file_path):
    try:
        df = pd.read_csv(file_path)
        st.success("✅ בסיס הנתונים נטען בהצלחה")
        
        # הצגת טבלה בסיסית רק כדי לראות שהכל עובד
        st.subheader("נתונים גולמיים מהמחסן:")
        st.write(df)
        
        # כאן אפשר להוסיף את שאר הגרפים אחרי שווידאנו שזה עובד
    except Exception as e:
        st.error(f"שגיאה בקריאת הקובץ: {e}")
else:
    st.error(f"קובץ הנתונים לא נמצא בנתיב: {file_path}")
    st.info("ודא שיש לך תיקייה בשם data ובתוכה קובץ בשם database.csv ב-GitHub")
