import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 1. הגדרת דף (חייבת להיות ראשונה) ---
st.set_page_config(
    page_title="Apex Pro - ניתוח דוחות ביטוח",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. עיצוב RTL (מימין לשמאל) ---
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
    .stTextInput > div > div > input { text-align: right; }
    .stSelectbox > div > div > div { text-align: right; }
    .stChatMessage { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- 3. כותרת ---
st.title("📊 Apex Pro - ניתוח דוחות ביטוח מתקדם")
st.caption("מופעל על ידי Gemini 1.5 Pro - המודל החזק ביותר לניתוח פיננסי")

# --- 4. הגדרת API ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ שגיאה: המפתח GOOGLE_API_KEY לא נמצא בקובץ ה-Secrets.")
    st.info("אנא גש להגדרות האפליקציה -> Secrets וודא שהמפתח מוגדר שם.")
    st.stop()

# --- 5. הגדרת המודל (PRO) ---
generation_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro", 
    generation_config=generation_config,
    system_instruction="""
    אתה אנליסט בכיר ורגולטור בתחום הביטוח בישראל. התמחותך היא בניתוח דוחות כספיים לפי תקני IFRS 17 ו-Solvency II.
    תפקידך לנתח קבצי PDF של דוחות כספיים (מאזן, רווח והפסד, דוח דירקטוריון).
    
    הנחיות קריטיות:
    1. התבסס אך ורק על המידע בקובץ. אל תמציא נתונים.
    2. אם המשתמש שואל על נתון (כמו הון עצמי) והוא לא מופיע בקובץ, ציין זאת במפורש.
    3. ענה בעברית מקצועית וברורה.
    4. הצג מספרים בפורמט קריא (עם פסיקים לאלפים).
    """
)

# --- 6. פונקציות עזר ---
def upload_to_gemini(path, mime_type="application/pdf"):
    file = genai.upload_file(path, mime_type=mime_type)
    return file

def wait_for_files_active(files):
    st.spinner('מעבד את הקובץ בשרתי Google AI...')
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")

# --- 7. ממשק משתמש (Sidebar) ---
with st.sidebar:
    st.header("הגדרות וקבצים")
    uploaded_file = st.file_uploader("העלה דוח כספי (PDF)", type=['pdf'])
    st.markdown("---")
    st.info("💡 טיפ: לתוצאות מדויקות, העלה את קובץ 'הדוחות הכספיים' המלא.")

# --- 8. לוגיקה ראשית ---
if uploaded_file:
    # שמירת קובץ זמני
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # שליחה לגוגל
        with st.spinner('מפענח את הדוח באמצעות Gemini Pro...'):
            gemini_file = upload_to_gemini(tmp_path)
            wait_for_files_active([gemini_file])
            
        st.success("✅ הקובץ נקלט בהצלחה! המערכת מוכנה.")

        # ניהול היסטוריית צ'אט
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # קלט משתמש
        if prompt := st.chat_input("שאל שאלה על הדוח..."):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                with st.spinner('מנתח...'):
                    try:
                        # כאן תוקנה השגיאה - נוסף סוגר סוגר בסוף הפקודה
                        response = model.generate_content(
                            [gemini_file, prompt],
                            request_options={"timeout": 600}
                        )
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"שגיאה בקבלת תשובה: {e}")

    except Exception as e:
        st.error(f"שגיאה בעיבוד הקובץ: {e}")
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

else:
    st.info("👈 נא להעלות קובץ PDF כדי להתחיל.")
