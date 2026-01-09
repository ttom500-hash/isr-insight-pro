import streamlit as st
import google.generativeai as genai
import sys

# --- 1. הגדרת דף (הגרסה המתוקנת ללא שגיאות) ---
st.set_page_config(page_title="בדיקת גרסה", layout="wide")

# עיצוב לימין (בצורה התקינה)
st.markdown("""<style>.stApp {direction: rtl;} h1, h2, p {text-align: right;}</style>""", unsafe_allow_html=True)

st.title("🛠️ בדיקת מנוע")

# --- 2. בדיקת גרסת הספרייה ---
try:
    current_version = genai.__version__
    st.metric(label="גרסת המנוע המותקנת (google-generativeai)", value=current_version)

    st.write("---")

    # בדיקה האם הגרסה תקינה (חייבת להיות 0.7.0 ומעלה)
    # המרת הגרסה למספרים להשוואה
    major, minor, patch = map(int, current_version.split('.')[:3])
    
    if (major == 0 and minor >= 7) or major >= 1:
        st.success("✅ **חדשות טובות:** הגרסה מעודכנת! (0.7.0 ומעלה)")
        version_ok = True
    else:
        st.error(f"❌ **הבעיה נמצאה:** הגרסה היא `{current_version}` (ישנה מדי).")
        st.info("זה אומר שהקובץ requirements.txt לא נקלט. צריך לעשות Reboot.")
        version_ok = False

except Exception as e:
    st.error(f"לא הצלחתי לבדוק גרסה: {e}")
    version_ok = False

# --- 3. בדיקת חיבור למודל (רק אם הגרסה תקינה) ---
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
