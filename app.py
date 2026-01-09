import streamlit as st

# --- 1. הגדרת דף (הגרסה המתוקנת) ---
st.set_page_config(page_title="בדיקת כספת", layout="wide")

# --- 2. עיצוב RTL (ככה עושים את זה נכון) ---
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 בדיקת כספת (Secrets Debugger)")

# --- 3. בדיקת תוכן הכספת ---
st.write("---")
st.write("בודק מה המערכת רואה בתוך ה-Secrets...")

try:
    # בדיקה האם הכספת ריקה
    if not st.secrets:
        st.error("❌ הכספת (st.secrets) ריקה לחלוטין!")
        st.info("זה אומר ששום מפתח לא נשמר. אנא נסה לשמור שוב דרך ההגדרות.")
    else:
        st.success("✅ הכספת לא ריקה! הנה המפתחות שמצאתי:")
        
        found_target_key = False
        
        # מעבר על כל המפתחות שנמצאו
        for key in st.secrets:
            # הצגת שם המפתח (בלי הערך עצמו)
            st.markdown(f"🗝️ מפתח קיים בשם: `{key}`")
            
            if key == "GOOGLE_API_KEY":
                found_target_key = True
                value = st.secrets[key]
                st.info("👍 בול! המפתח `GOOGLE_API_KEY` נמצא.")
                
                # בדיקת תקינות בסיסית
                if value:
                    st.write(f"אורך המפתח: {len(value)} תווים")
                    st.write(f"התחלה: `{value[:5]}...`")
                    st.write(f"סוף: `...{value[-5:]}`")
                    
                    if " " in value:
                        st.warning("⚠️ שים לב: יש רווחים בתוך המפתח. זה עלול לגרום לבעיות.")
                    elif len(value) < 30:
                        st.warning("⚠️ שים לב: המפתח נראה קצר מדי.")
                    else:
                        st.success("✨ המבנה נראה תקין לחלוטין.")
                else:
                    st.error("הערך של המפתח ריק!")

        if not found_target_key:
            st.error("❌ לא נמצא מפתח בשם `GOOGLE_API_KEY`.")
            st.write("המפתחות שיש לך כרגע הם:")
            st.code(list(st.secrets.keys()))

except FileNotFoundError:
    st.error("קובץ ה-Secrets לא נמצא בכלל.")
