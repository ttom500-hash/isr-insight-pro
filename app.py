import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 1. הגדרת דף ---
st.set_page_config(page_title="Apex Pro", layout="wide")

# --- 2. עיצוב RTL ---
st.markdown("""
<style>
    .stApp { direction: rtl; }
    h1, h2, h3, p, div { text-align: right; }
    .stTextInput > div > div > input { text-align: right; }
    .stChatMessage { direction: rtl; text-align: right; }
    p { text-align: right; }
</style>
""", unsafe_allow_html=True)

st.title("🏢 Apex Pro - אנליסט חכם")

# --- 3. חיבור לגוגל ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ חסר מפתח ב-Secrets.")
    st.stop()

# חיבור ראשוני
genai.configure(api_key=api_key)

# --- מנגנון "טייס אוטומטי" למציאת מודל תקין ---
@st.cache_resource
def find_working_model():
    try:
        # בקשת רשימת המודלים הזמינים לך
        models = list(genai.list_models())
        
        # חיפוש מודל לפי סדר עדיפות
        priority_list = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]
        
        # בדיקה: האם אחד מהמועדפים קיים ברשימה?
        for priority in priority_list:
            for m in models:
                if priority in m.name and 'generateContent' in m.supported_generation_methods:
                    return m.name # מצאנו!
        
        # אם לא מצאנו מועדף, ניקח את הראשון שעובד
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                return m.name
                
        return None
    except Exception as e:
        st.error(f"שגיאה באיתור מודלים: {e}")
        return None

# בחירת המודל
model_name = find_working_model()

if model_name:
    st.caption(f"מחובר למודל: {model_name}")
    model = genai.GenerativeModel(model_name)
else:
    st.error("❌ המפתח תקין, אך לא נמצאו מודלים זמינים בחשבון זה.")
    st.stop()

# --- 4. פונקציית העלאה ---
def upload_file(path):
    msg = st.toast("מעלה קובץ לענן המאובטח...", icon="⏳")
    
    try:
        file = genai.upload_file(path, mime_type="application/pdf")
        
        # המתנה לעיבוד
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(file.name)
            
        if file.state.name != "ACTIVE":
            raise Exception(f"העיבוד נכשל (סטטוס: {file.state.name})")
            
        msg.toast("הדוח מוכן לעבודה!", icon="✅")
        return file
    except Exception as e:
        st.error(f"תקלה בהעלאת הקובץ: {e}")
        return None

# --- 5. צד ימין (בחירת קובץ) ---
base_path = "data/Insurance_Warehouse"
selected_file = None

with st.sidebar:
    st.header("מקור הנתונים")
    mode = st.radio("בחר:", ["ארכיון (GitHub)", "העלאה ידנית"])
    
    if mode == "ארכיון (GitHub)":
        if os.path.exists(base_path):
            companies = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
            if companies:
                comp = st.selectbox("חברה", companies)
                y_path = os.path.join(base_path, comp)
                years = [d for d in os.listdir(y_path) if os.path.isdir(os.path.join(y_path, d))] if os.path.exists(y_path) else ["2025"]
                year = st.selectbox("שנה", years)
                q = st.selectbox("רבעון", ["Q1", "Q2", "Q3", "Q4"])
                
                final_dir = os.path.join(base_path, comp, year, q, "Financial_Reports")
                if os.path.exists(final_dir):
                    files = [f for f in os.listdir(final_dir) if f.endswith(".pdf")]
                    if files:
                        fname = st.selectbox("דוח", files)
                        selected_file = os.path.join(final_dir, fname)
                    else: st.warning("אין קבצים")
                else: st.warning("תיקייה ריקה")
        else: st.error("תיקיית data לא נמצאה")
    else:
        up = st.file_uploader("גרור PDF", type=['pdf'])
        if up:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                t.write(up.getvalue())
                selected_file = t.name

# --- 6. צ'אט ---
if selected_file:
    if "curr_file" not in st.session_state or st.session_state.curr_file != selected_file:
        st.session_state.g_file = upload_file(selected_file)
        if st.session_state.g_file:
            st.session_state.curr_file = selected_file
            st.session_state.history = []

    for msg in st.session_state.get("history", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("שאל שאלה..."):
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.history.append({"role": "user", "content": prompt})

        if "g_file" in st.session_state:
            with st.chat_message("assistant"):
                with st.spinner("מעבד..."):
                    try:
                        response = model.generate_content([st.session_state.g_file, prompt], stream=True)
                        full_text = ""
                        ph = st.empty()
                        for chunk in response:
                            if chunk.text:
                                full_text += chunk.text
                                ph.markdown(full_text + "▌")
                        ph.markdown(full_text)
                        st.session_state.history.append({"role": "assistant", "content": full_text})
                    except Exception as e:
                        st.error(f"שגיאה: {e}")
