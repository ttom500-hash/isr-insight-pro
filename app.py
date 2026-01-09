import streamlit as st
import google.generativeai as genai
import google.api_core.exceptions
import tempfile
import os
import time

# --- 1. הגדרת דף ---
st.set_page_config(
    page_title="Apex Pro Debugger",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. עיצוב RTL ---
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
    .stTextInput > div > div > input { text-align: right; }
    .stChatMessage { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

st.title("🛠️ Apex Pro - מצב בדיקה")

# --- 3. בדיקת מפתח ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # st.success("המפתח זוהה במערכת") # הוסר כדי לא להעמיס
else:
    st.error("❌ מפתח API חסר. בדוק את ה-Secrets.")
    st.stop()

# --- 4. הגדרת מודל ---
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro", 
    generation_config={"temperature": 0.1},
    system_instruction="אתה אנליסט ביטוח. ענה בעברית."
)

# --- 5. פונקציות ---
def upload_to_gemini(path):
    st.write(f"DEBUG: מתחיל העלאה של {path}...")
    file = genai.upload_file(path, mime_type="application/pdf")
    while file.state.name == "PROCESSING":
        time.sleep(1)
        file = genai.get_file(file.name)
    if file.state.name != "ACTIVE":
        raise Exception(f"הקובץ נכשל: {file.state.name}")
    st.write("DEBUG: הקובץ עלה והוא ACTIVE")
    return file

# --- 6. צד ימין ---
base_path = "data/Insurance_Warehouse" 
selected_file_path = None

with st.sidebar:
    st.header("בדיקת קבצים")
    mode = st.radio("בחר:", ["GitHub", "ידני"])
    
    if mode == "GitHub":
        if os.path.exists(base_path):
            companies = os.listdir(base_path)
            if companies:
                comp = st.selectbox("חברה", companies)
                # נתיב קשיח לבדיקה - נסה למצוא קובץ ראשון
                year_path = os.path.join(base_path, comp, "2025", "Q1", "Financial_Reports")
                if os.path.exists(year_path):
                    files = [f for f in os.listdir(year_path) if f.endswith(".pdf")]
                    if files:
                        f = st.selectbox("קובץ", files)
                        selected_file_path = os.path.join(year_path, f)
                    else:
                        st.warning("אין קבצים בתיקייה")
                else:
                    st.warning(f"נתיב לא קיים: {year_path}")
        else:
            st.error("אין תיקיית דאטה")
    else:
        uploaded = st.file_uploader("העלה קובץ")
        if uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.getvalue())
                selected_file_path = tmp.name

# --- 7. לוגיקה ראשית ---
if selected_file_path:
    # טעינה
    if "current_path" not in st.session_state or st.session_state.current_path != selected_file_path:
        st.info("🔄 טוען קובץ חדש...")
        try:
            gemini_file = upload_to_gemini(selected_file_path)
            st.session_state.gemini_file = gemini_file
            st.session_state.current_path = selected_file_path
            st.session_state.messages = []
            st.success("✅ קובץ נטען!")
        except Exception as e:
            st.error(f"שגיאה בטעינה: {e}")

    # צ'אט
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # קלט
    if prompt := st.chat_input("כתוב שאלה..."):
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # הדפסת דיבאג למסך כדי שתראה שזה עובד
        debug_msg = st.empty()
        debug_msg.info("⏳ שולח בקשה לגוגל... נא להמתין")

        if "gemini_file" in st.session_state:
            try:
                # שימוש ב-stream=False לבדיקה ראשונית (יותר יציב לפעמים)
                response = model.generate_content([st.session_state.gemini_file, prompt])
                
                debug_msg.empty() # מחיקת הודעת ההמתנה
                
                st.chat_message("assistant").write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            except Exception as e:
                debug_msg.error(f"❌ שגיאה בקבלת תשובה: {e}")
        else:
            st.error("אין קובץ בזיכרון")

else:
    st.info("בחר קובץ")
