import streamlit as st
import google.generativeai as genai
import tempfile
import os
import time

# --- 1. הגדרת דף ---
st.set_page_config(page_title="Apex Pro", layout="wide")
st.markdown("""<style>.stApp {direction: rtl;} h1, h2, h3, p, div {text-align: right;} 
.stTextInput>div>div>input {text-align: right;} .stChatMessage {direction: rtl; text-align: right;}</style>""", unsafe_allow_html=True)

st.title("🏢 Apex Pro - אנליסט חכם")

# --- 2. מנגנון איתור מפתח חכם 🕵️‍♂️ ---
api_key = None
# ניסיון 1: השם הרשמי
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
# ניסיון 2: השם הישן
elif "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

# בדיקה האם נמצא מפתח
if not api_key:
    st.error("❌ לא נמצא מפתח מתאים ב-Secrets.")
    st.write("המערכת חיפשה: `GOOGLE_API_KEY` או `GEMINI_API_KEY`")
    
    # הצגת מה שכן קיים (כדי לעזור לך למצוא את הטעות)
    if st.secrets:
        st.warning("⚠️ המפתחות שכן נמצאו בכספת הם:")
        st.code(list(st.secrets.keys()))
        st.info("אם השם שונה, נא לשנות אותו ב-Secrets לשם התקני: GOOGLE_API_KEY")
    else:
        st.error("הכספת ריקה לחלוטין! וודא שלחצת על Save.")
    
    st.stop()

# --- 3. חיבור ואיתור מודל ---
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    # רשימת עדיפויות
    candidates = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    try:
        my_models = [m.name for m in genai.list_models()]
        # בדיקה האם המועדפים קיימים
        for cand in candidates:
            full_name = f"models/{cand}"
            if full_name in my_models:
                return cand
        return "gemini-1.5-flash" # ברירת מחדל
    except:
        return "gemini-1.5-flash"

model_name = get_model()
st.caption(f"מחובר למודל: {model_name}")
model = genai.GenerativeModel(model_name)

# --- 4. פונקציית העלאה ---
def upload_file(path):
    msg = st.toast("מעלה...", icon="⏳")
    try:
        file = genai.upload_file(path, mime_type="application/pdf")
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(file.name)
        if file.state.name != "ACTIVE":
            raise Exception("עיבוד נכשל")
        msg.toast("מוכן!", icon="✅")
        return file
    except Exception as e:
        st.error(f"תקלה: {e}")
        return None

# --- 5. ממשק משתמש ---
base_path = "data/Insurance_Warehouse"
selected_file = None

with st.sidebar:
    st.header("נתונים")
    mode = st.radio("מקור:", ["GitHub", "העלאה ידנית"])
    if mode == "GitHub":
        if os.path.exists(base_path):
            comp = st.selectbox("חברה", os.listdir(base_path))
            # זיהוי שנה
            yp = os.path.join(base_path, comp)
            years = [d for d in os.listdir(yp) if os.path.isdir(os.path.join(yp, d))] if os.path.exists(yp) else ["2025"]
            year = st.selectbox("שנה", years)
            q = st.selectbox("רבעון", ["Q1", "Q2", "Q3", "Q4"])
            final_dir = os.path.join(base_path, comp, year, q, "Financial_Reports")
            if os.path.exists(final_dir):
                files = [f for f in os.listdir(final_dir) if f.endswith(".pdf")]
                if files:
                    fname = st.selectbox("דוח", files)
                    selected_file = os.path.join(final_dir, fname)
    else:
        up = st.file_uploader("PDF", type=['pdf'])
        if up:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t:
                t.write(up.getvalue())
                selected_file = t.name

# --- 6. צ'אט ---
if selected_file:
    if "curr" not in st.session_state or st.session_state.curr != selected_file:
        st.session_state.gf = upload_file(selected_file)
        if st.session_state.gf:
            st.session_state.curr = selected_file
            st.session_state.hist = []

    for m in st.session_state.get("hist", []):
        st.chat_message(m["role"]).write(m["content"])

    if p := st.chat_input("שאל שאלה..."):
        st.chat_message("user").write(p)
        st.session_state.hist.append({"role": "user", "content": p})
        
        with st.chat_message("assistant"):
            with st.spinner("חושב..."):
                try:
                    res = model.generate_content([st.session_state.gf, p], stream=True)
                    full = ""
                    ph = st.empty()
                    for c in res:
                        if c.text:
                            full += c.text
                            ph.markdown(full + "▌")
                    ph.markdown(full)
                    st.session_state.hist.append({"role": "assistant", "content": full})
                except Exception as e:
                    st.error(str(e))
