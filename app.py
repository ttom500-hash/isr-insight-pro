import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 1. הגדרת דף ---
st.set_page_config(page_title="Apex Pro", layout="wide")

# --- 2. עיצוב RTL (מתוקן) ---
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
st.caption("v0.8.6 | Flash Model")

# --- 3. חיבור לגוגל ---
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("חסר מפתח ב-Secrets")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- 4. פונקציית העלאה ---
def upload_file(path):
    msg = st.toast("מעלה קובץ...", icon="⏳")
    file = genai.upload_file(path, mime_type="application/pdf")
    while file.state.name == "PROCESSING":
        time.sleep(1)
        file = genai.get_file(file.name)
    if file.state.name != "ACTIVE":
        raise Exception("העיבוד נכשל")
    msg.toast("הדוח מוכן לעבודה!", icon="✅")
    return file

# --- 5. צד ימין (בחירת קובץ) ---
base_path = "data/Insurance_Warehouse"
selected_file = None

with st.sidebar:
    st.header("מקור הנתונים")
    mode = st.radio("בחר:", ["ארכיון (GitHub)", "העלאה ידנית"])
    
    if mode == "ארכיון (GitHub)":
        if os.path.exists(base_path):
            comp = st.selectbox("חברה", os.listdir(base_path))
            year = st.selectbox("שנה", ["2025"]) # פשוט יותר לבדיקה
            q = st.selectbox("רבעון", ["Q1"])
            
            final_dir = os.path.join(base_path, comp, year, q, "Financial_Reports")
            if os.path.exists(final_dir):
                files = [f for f in os.listdir(final_dir) if f.endswith(".pdf")]
                if files:
                    fname = st.selectbox("דוח", files)
                    selected_file = os.path.join(final_dir, fname)
    else:
        up = st.file_uploader("גרור PDF", type=['pdf'])
        if up:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                t.write(up.getvalue())
                selected_file = t.name

# --- 6. צ'אט (החלק שתוקן) ---
if selected_file:
    # טעינה ראשונית
    if "curr_file" not in st.session_state or st.session_state.curr_file != selected_file:
        try:
            st.session_state.g_file = upload_file(selected_file)
            st.session_state.curr_file = selected_file
            st.session_state.history = []
        except Exception as e:
            st.error(f"תקלה בטעינה: {e}")

    # הצגת היסטוריה
    for msg in st.session_state.get("history", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # קלט משתמש
    if prompt := st.chat_input("שאל שאלה על הדוח..."):
        # 1. הצג את שאלת המשתמש מיד
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.history.append({"role": "user", "content": prompt})

        # 2. הצג חיווי שהמערכת חושבת
        with st.chat_message("assistant"):
            with st.spinner("מעבד נתונים..."):
                try:
                    # שליחה לגוגל
                    response = model.generate_content([st.session_state.g_file, prompt], stream=True)
                    
                    # הדפסת התשובה תוך כדי כתיבה
                    full_text = ""
                    placeholder = st.empty()
                    for chunk in response:
                        if chunk.text:
                            full_text += chunk.text
                            placeholder.markdown(full_text + "▌")
                    placeholder.markdown(full_text)
                    
                    # שמירה בהיסטוריה
                    st.session_state.history.append({"role": "assistant", "content": full_text})
                    
                except Exception as e:
                    st.error(f"שגיאה: {e}")
