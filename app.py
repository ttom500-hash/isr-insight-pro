import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- הגדרת דף (חייבת להיות ראשונה) ---
st.set_page_config(
    page_title="Apex Pro - ניתוח דוחות ביטוח",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- עיצוב RTL (מימין לשמאל) ---
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
    .stTextInput > div > div > input { text-align: right; }
    .stSelectbox > div > div > div { text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- כותרת ראשית ---
st.title("📊 Apex Pro - ניתוח דוחות ביטוח מתקדם")
st.caption("מופעל על ידי Gemini 1.5 Pro - המודל החזק ביותר לניתוח פיננסי")

# --- הגדרת API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ מפתח API חסר. נא להגדיר אותו ב-Streamlit Secrets.")
    st.stop()

# --- הגדרת המודל (החלק החשוב ביותר!) ---
generation_config = {
    "temperature": 0.2,       # דיוק מקסימלי, פחות יצירתיות
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192, # תשובות ארוכות ומפורטות
    "response_mime_type": "text/plain",
}

# שימוש במודל PRO לקריאת מסמכים אופטימלית
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro", 
    generation_config=generation_config,
    system_instruction="""
    אתה אנליסט בכיר ורגולטור בתחום הביטוח בישראל. התמחותך היא בניתוח דוחות כספיים לפי תקני IFRS 17 ו-Solvency II.
    תפקידך לנתח קבצי PDF של דוחות כספיים (מאזן, רווח והפסד, דוח דירקטוריון).
    
    הנחיות קריטיות:
    1. התבסס אך ורק על המידע בקובץ. אל תמציא נתונים.
    2. אם המשתמש שואל על נתון (כמו הון עצמי) והוא לא מופיע בקובץ (למשל, כי זה רק דוח מילולי ללא המאזן המלא), ציין זאת במפורש: "הנתון אינו מופיע בקובץ זה, ייתכן והוא נמצא בדוחות הכספיים המלאים ולא בדוח הדירקטוריון".
    3. ענה בעברית מקצועית וברורה.
    4. הצג מספרים בפורמט קריא (עם פסיקים לאלפים).
    """
)

# --- פונקציות עזר לטיפול בקבצים ---
def upload_to_gemini(path, mime_type="application/pdf"):
    """מעלה את הקובץ לשרתים של גוגל לעיבוד"""
    file = genai.upload_file(path, mime_type=mime_type)
    return file

def wait_for_files_active(files):
    """ממתין שהקובץ יהיה מוכן לעיבוד בצד של גוגל"""
    st.spinner('מעבד את הקובץ בשרתי Google AI...')
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            time.sleep(2) # בדיקה כל 2 שניות
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")

# --- ממשק המשתמש ---
with st.sidebar:
    st.header("הגדרות וקבצים")
    uploaded_file = st.file_uploader("העלה דוח כספי (PDF)", type=['pdf'])
    
    st.markdown("---")
    st.info("💡 טיפ: לקבלת נתונים מדויקים על הון עצמי ומאזן, וודא שאתה מעלה את הקובץ המלא של **הדוחות הכספיים** ולא רק את דוח הדירקטוריון.")

# --- לוגיקה ראשית ---
if uploaded_file:
    # שמירת הקובץ באופן זמני
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # העלאה לגוגל
        with st.spinner('מעלה את הקובץ ומפענח נתונים (מודל Pro)...'):
            gemini_file = upload_to_gemini(tmp_path)
            wait_for_files_active([gemini_file])
            
        st.success("✅ הקובץ פוענח בהצלחה! אפשר לשאול שאלות.")

        # היסטוריית צ'אט
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # קלט משתמש
        if prompt := st.chat_input("שאל שאלה על הדוח (למשל: מהו הרווח הכולל? מה יחס כושר הפירעון?)"):
            # הצגת שאלת המשתמש
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # יצירת תשובה
            with st.chat_message("assistant"):
                with st.spinner('מנתח נתונים...'):
                    # שליחת הקובץ + השאלה למודל
                    response = model.generate_content(
                        [gemini_file, prompt],
                        request_options={"timeout": 600} # זמן המתנה ארוך לקבצים גדולים
                    )
                    st.markdown(response.text)
            
            st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"שגיאה בעיבוד הקובץ: {e}")
        
    finally:
        # ניקוי קובץ זמני
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

else:
    st.info("👈 אנא העלה קובץ PDF בצד ימין כדי להתחיל.")
