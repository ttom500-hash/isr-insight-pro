import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions
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
    /* הסתרת כפתור ה-deploy של סטרימליט שיהיה נקי */
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# --- 3. כותרת ---
st.title("🏢 Apex Pro Enterprise - מערכת ניתוח דוחות")

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
    generation_config={"temperature": 0.1}, # טמפרטורה נמוכה לדיוק בנתונים
    system_instruction="אתה אנליסט ביטוח בכיר. התמחותך היא ב-IFRS 17 ו-Solvency II. ענה בעברית מקצועית ותמציתית."
)

# --- 6. פונקציות עזר ---
def get_available_companies(base_path):
    if not os.path.exists(base_path):
        return []
    return [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

def upload_to_gemini(path):
    """מעלה קובץ לגוגל ומחזיר את האובייקט"""
    file = genai.upload_file(path, mime_type="application/pdf")
    # המתנה לעיבוד
    while file.state.name == "PROCESSING":
        time.sleep(1)
        file = genai.get_file(file.name)
    if file.state.name != "ACTIVE":
        raise Exception(f"הקובץ נכשל בעיבוד: {file.state.name}")
    return file

# --- 7. ניהול בחירת קובץ (צד ימין) ---
base_path = "data/Insurance_Warehouse" 

with st.sidebar:
    st.header("🗄️ ארכיון דוחות")
    companies = get_available_companies(base_path)
    
    selected_file_path = None
    
    if companies:
        col1, col2 = st.columns(2)
        with col1:
            company = st.selectbox("חברה", companies)
        with col2:
            year = st.selectbox("שנה", ["2025", "2024"])
            
        quarter = st.selectbox("רבעון", ["Q1", "Q2", "Q3", "Q4"])
        
        # נתיב חיפוש
        search_path = os.path.join(base_path, company, year, quarter, "Financial_Reports")
        
        if os.path.exists(search_path):
            files = [f for f in os.listdir(search_path) if f.endswith(".pdf")]
            if files:
                selected_filename = st.selectbox("בחר דוח PDF", files)
                selected_file_path = os.path.join(search_path, selected_filename)
            else:
                st.warning("לא נמצאו קבצים בתיקייה זו")
        else:
            st.warning("טרם הועלו דוחות לתקופה זו")
    else:
        st.info("מצב ידני (לא נמצא ארכיון)")
        uploaded_user_file = st.file_uploader("העלה דוח", type=['pdf'])

# --- 8. לוגיקה חכמה לטעינת קובץ (מונעת ניתוקים) ---
current_file = None

# קביעת הקובץ הסופי לעבודה
final_path_to_process = selected_file_path
if not final_path_to_process and 'uploaded_user_file' in locals() and uploaded_user_file:
    # טיפול בקובץ ידני
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_user_file.getvalue())
        final_path_to_process = tmp.name

# מנגנון טעינה אוטומטי (Auto-Load)
if final_path_to_process:
    # אם החלפנו קובץ, או שאין קובץ בזיכרון - נעלה חדש
    if "current_file_path" not in st.session_state or st.session_state.current_file_path != final_path_to_process:
        with st.spinner(f'מנתח את הדוח: {os.path.basename(final_path_to_process)}...'):
            try:
                gemini_file = upload_to_gemini(final_path_to_process)
                st.session_state.gemini_file = gemini_file
                st.session_state.current_file_path = final_path_to_process
                st.session_state.chat_history = [] # איפוס צ'אט כשמחליפים דוח
                st.success("✅ הדוח נטען ומוכן לניתוח")
            except Exception as e:
                st.error(f"שגיאה בטעינת הקובץ: {e}")
    
    # שליפה מהזיכרון
    if "gemini_file" in st.session_state:
        current_file = st.session_state.gemini_file

# --- 9. אזור הצ'אט ---
if current_file:
    # הצגת היסטוריה
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    # קלט משתמש
    if prompt := st.chat_input("שאל שאלה על הדוח (למשל: מה הרווח הכולל?)..."):
        st.chat_message("user").write(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner('מעבד נתונים...'):
                try:
                    # כאן התיקון הגדול - טיפול בשגיאת התנתקות
                    response = model.generate_content([current_file, prompt])
                    st.write(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                
                except google.api_core.exceptions.NotFound:
                    # אם הקובץ התנתק, ננסה להעלות אותו שוב אוטומטית בפעם הבאה
                    st.error("⚠️ הקשר עם הקובץ אבד (Time out). המערכת תטען אותו מחדש אוטומטית.")
                    # מחיקת הזיכרון כדי לכפות טעינה מחדש בלחיצה הבאה
                    del st.session_state['current_file_path']
                    st.rerun() # רענון אוטומטי לטעינה מחדש
                
                except Exception as e:
                    st.error(f"אירעה שגיאה: {e}")

else:
    st.info("👈 בחר דוח מהתפריט בצד ימין כדי להתחיל.")
