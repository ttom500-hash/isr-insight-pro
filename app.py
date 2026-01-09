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

# --- 2. איתור מפתח חכם (בודק את כל האפשרויות) ---
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ לא נמצא מפתח ב-Secrets.")
    st.info("הקוד מחפש: GOOGLE_API_KEY או GEMINI_API_KEY")
    # הצגת מה שכן יש (לצורך דיבוג בלבד)
    if st.secrets:
        st.warning(f"המפתחות הקיימים כרגע הם: {list(st.secrets.keys())}")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. איתור מודל אוטומטי (למניעת שגיאת 404) ---
@st.cache_resource
def get_best_model():
    try:
        available_models = list(genai.list_models())
        text_models = [m for m in available_models if 'generateContent' in m.supported_generation_methods]
        
        if not text_models:
            return None, "לא נמצאו מודלים."
            
        # עדיפות ל-Flash
        for m in text_models:
            if "flash" in m.name.lower():
                return m.name, "Flash ⚡"
        
        # עדיפות ל-Pro
        for m in text_models:
            if "pro" in m.name.lower():
                return m.name, "Pro 🧠"
                
        return text_models[0].name, "Standard"
        
    except Exception as e:
        return None, str(e)

model_name, model_desc = get_best_model()

if model_name:
    st.caption(f"מחובר למודל: {model_name} ({model_desc})")
    model = genai.GenerativeModel(model_name)
else:
    st.error(f"תקלה באיתור מודל: {model_desc}")
    st.stop()

# --- 4. פונקציית העלאה ---
def upload_file(path):
    msg = st.toast("מעלה קובץ...", icon="⏳")
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
