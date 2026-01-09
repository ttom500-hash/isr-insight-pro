import streamlit as st
import google.generativeai as genai
import sys

st.set_page_config(page_title="בדיקת טכנאי", direction="rtl")
st.title("🛠️ בדיקת גרסה ומנוע")

# 1. בדיקת גרסת הספרייה (האם השדרוג הצליח?)
try:
    current_version = genai.__version__
    st.metric(label="גרסת המנוע (google-generativeai)", value=current_version)

    st.write("---")

    # בדיקה האם הגרסה תקינה
    if current_version >= "0.7.0":
        st.success("✅ **חדשות טובות:** הגרסה מעודכנת! הקובץ requirements.txt נקלט בהצלחה.")
        version_ok = True
    else:
        st.error(f"❌ **הבעיה נמצאה:** הגרסה המותקנת היא `{current_version}` (ישנה מדי).")
        st.info("הפתרון: השרת עדיין לא ביצע את העדכון שביקשת. צריך לעשות Reboot App שוב.")
        version_ok = False

except Exception as e:
    st.error("לא הצלחתי לבדוק את הגרסה.")
    version_ok = False

# 2. בדיקת חיבור למודל (רק אם הגרסה תקינה)
if version_ok:
    st.write("בדיקת חיבור למודל Flash...")
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    if api_key:
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Test")
            st.success("🎉 **הכל עובד!** המודל הגיב בהצלחה.")
            st.balloons()
        except Exception as e:
            st.error("הגרסה טובה, אבל המודל לא מגיב:")
            st.code(str(e))
    else:
        st.warning("לא נמצא מפתח ב-Secrets.")
