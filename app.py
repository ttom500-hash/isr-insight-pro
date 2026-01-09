import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 1. הגדרת דף ---
st.set_page_config(
    page_title="Apex Pro Enterprise",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. עיצוב RTL ---
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
st.title("🏢 Apex Pro Enterprise - ניתוח דוחות ארגוני")
st.caption("מחובר למאגר הנתונים הארגוני (Data Warehouse)")

# --- 4. הגדרת API ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ מפתח API חסר ב-Secrets.")
    st.stop()

# --- 5. הגדרת המודל ---
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro", 
    generation_config={"temperature": 0.2},
    system_instruction="אתה אנליסט ביטוח בכיר. נתח את הדוחות לפי IFRS 17 ו-Solvency II."
)

# --- 6. פונקציות עזר ---
def get_available_companies(base_path):
    if not os.path.exists(base_path):
        return []
    return [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

def upload_to_gemini(path):
    return genai.upload_file(path, mime_type="application/pdf")

def wait_for_files_active(files):
    st.spinner('מעבד קובץ...')
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            time.sleep(2)
            file = genai.get_file(name)

# --- 7. צד ימין: בחירת קובץ מהספרייה ---
base_path = "data/Insurance_Warehouse" # הנתיב לתיקיות שלך

with st.sidebar:
    st.header("🗄️ ספריית דוחות")
    
    # בדיקה אם התיקייה קיימת
    companies = get_available_companies(base_path)
    
    selected_file_path = None
    
    if companies:
        company = st.selectbox("בחר חברה", companies)
        year = st.selectbox("בחר שנה", ["2025", "2024"]) # אפשר לשכלל שזה יהיה דינמי
        quarter = st.selectbox("בחר רבעון", ["Q1", "Q2", "Q3", "Q4"])
        
        # בניית הנתיב לקובץ
        # מחפש בתיקיית Financial_Reports
        search_path = os.path.join(base_path, company, year, quarter, "Financial_Reports")
        
        if os.path.exists(search_path):
            files = [f for f in os.listdir(search_path) if f.endswith(".pdf")]
            if files:
                selected_filename = st.selectbox("בחר דוח", files)
                selected_file_path = os.path.join(search_path, selected_filename)
                st.success(f"נמצא: {selected_filename}")
            else:
                st.warning("לא נמצאו קבצי PDF בתיקייה זו")
        else:
            st.warning("הנתיב לא קיים (עדיין לא הועלו דוחות לרבעון זה)")
            
    else:
        st.info("לא נמצאה תיקיית 'Insurance_Warehouse'. המערכת עוברת למצב העלאה ידנית.")
        uploaded_user_file = st.file_uploader("העלה דוח ידנית", type=['pdf'])

# --- 8. לוגיקה ראשית ---
# משתמשים בקובץ מהספרייה או בקובץ שהועלה ידנית
final_file_path = None

if selected_file_path:
    final_file_path = selected_file_path
elif 'uploaded_user_file' in locals() and uploaded_user_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_user_file.getvalue())
        final_file_path = tmp_file.name

# אם יש קובץ (מהספרייה או ידני) - מתחילים לעבוד
if final_file_path:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # כפתור להתחלת ניתוח
    if st.button("🚀 התחל ניתוח לדוח זה"):
        try:
            with st.spinner('שולח למודל Gemini Pro...'):
                gemini_file = upload_to_gemini(final_file_path)
                wait_for_files_active([gemini_file])
                st.session_state.gemini_file = gemini_file
                st.success("הדוח מוכן לשאלות!")
        except Exception as e:
            st.error(f"שגיאה: {e}")

    # אזור הצ'אט
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("שאל משהו על הדוח..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        if "gemini_file" in st.session_state:
            with st.chat_message("assistant"):
                with st.spinner('חושב...'):
                    response = model.generate_content([st.session_state.gemini_file, prompt])
                    st.write(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        else:
            st.warning("נא ללחוץ על 'התחל ניתוח' קודם.")

else:
    st.info("👈 בחר דוח מהספרייה בצד ימין (או העלה קובץ ידנית) כדי להתחיל.")
