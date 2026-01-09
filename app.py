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
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# --- 3. כותרת ---
st.title("🏢 Apex Pro - מערכת ניתוח דוחות")
st.caption("מופעל על ידי Gemini 1.5 Flash - המהיר ביותר")

# --- 4. הגדרת API ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ מפתח API חסר ב-Secrets.")
    st.stop()

# --- 5. הגדרת המודל (התיקון: מעבר ל-Flash) ---
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # <--- כאן השינוי החשוב!
    generation_config={"temperature": 0.1},
    system_instruction="אתה אנליסט ביטוח בכיר. התמחותך היא ב-IFRS 17 ו-Solvency II. ענה בעברית מקצועית, ברורה ותמציתית."
)

# --- 6. פונקציות עזר ---
def upload_to_gemini(path):
    """מעלה קובץ לגוגל ומחזיר את האובייקט"""
    # הדפסת דיבאג קטנה למסך
    status_placeholder = st.empty()
    status_placeholder.info("🚀 מעלה קובץ לענן...")
    
    file = genai.upload_file(path, mime_type="application/pdf")
    
    # המתנה לעיבוד
    while file.state.name == "PROCESSING":
        time.sleep(1)
        file = genai.get_file(file.name)
        
    if file.state.name != "ACTIVE":
        status_placeholder.error("❌ הקובץ נכשל בעיבוד")
        raise Exception(f"הקובץ נכשל בעיבוד: {file.state.name}")
    
    status_placeholder.empty() # ניקוי הודעה
    return file

# --- 7. צד ימין: ניהול קבצים ---
base_path = "data/Insurance_Warehouse" 

with st.sidebar:
    st.header("🗄️ מקור הנתונים")
    
    mode = st.radio("בחר מצב:", ["ארכיון (GitHub)", "העלאה ידנית"])
    
    selected_file_path = None
    uploaded_user_file = None

    if mode == "ארכיון (GitHub)":
        if os.path.exists(base_path):
            companies = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
            if companies:
                col1, col2 = st.columns(2)
                with col1:
                    company = st.selectbox("חברה", companies)
                with col2:
                    year_path = os.path.join(base_path, company)
                    years = [d for d in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, d))] if os.path.exists(year_path) else ["2025"]
                    year = st.selectbox("שנה", years)
                    
                quarter = st.selectbox("רבעון", ["Q1", "Q2", "Q3", "Q4"])
                
                search_path = os.path.join(base_path, company, year, quarter, "Financial_Reports")
                
                if os.path.exists(search_path):
                    files = [f for f in os.listdir(search_path) if f.endswith(".pdf")]
                    if files:
                        selected_filename = st.selectbox("בחר דוח", files)
                        selected_file_path = os.path.join(search_path, selected_filename)
                    else:
                        st.warning("אין קבצי PDF בתיקייה זו.")
                else:
                    st.warning("התיקייה ריקה.")
            else:
                st.warning("הארכיון ריק.")
        else:
            st.error("תיקיית הארכיון לא נמצאה.")
            
    else:
        uploaded_user_file = st.file_uploader("גרור לכאן דוח כספי", type=['pdf'])

# --- 8. לוגיקה ראשית ---
final_path_to_process = selected_file_path

# טיפול בקובץ ידני
if uploaded_user_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_user_file.getvalue())
        final_path_to_process = tmp.name

# מנגנון טעינה אוטומטי
if final_path_to_process:
    # בדיקה אם צריך לטעון מחדש
    if "current_file_path" not in st.session_state or st.session_state.current_file_path != final_path_to_process:
        try:
            gemini_file = upload_to_gemini(final_path_to_process)
            st.session_state.gemini_file = gemini_file
            st.session_state.current_file_path = final_path_to_process
            st.session_state.chat_history = [] 
            st.toast("✅ הדוח מחובר!", icon="⚡")
        except Exception as e:
            st.error(f"שגיאה בטעינה: {e}")
    
    # שליפה מהזיכרון
    if "gemini_file" in st.session_state:
        current_file = st.session_state.gemini_file

        # הצגת היסטוריה
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        # קלט משתמש
        if prompt := st.chat_input("שאל משהו על הדוח..."):
            st.chat_message("user").write(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                try:
                    # הזרמת תשובה (Streaming)
                    response = model.generate_content([current_file, prompt], stream=True)
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                
                except Exception as e:
                    message_placeholder.error(f"שגיאה: {e}")

else:
    st.info("👈 בחר דוח כדי להתחיל.")
