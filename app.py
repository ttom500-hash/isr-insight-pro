import os
import streamlit as st
import fitz  # PyMuPDF
import json
import urllib.request # שימוש בספריה בסיסית שעוקפת בעיות התקנה
import urllib.error

st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# ==========================================
# 1. המוח הגמיש (מנסה 3 מודלים שונים)
# ==========================================
def ask_google_direct(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: חסר מפתח API ב-Secrets"
    
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # רשימת מודלים לניסיון - אחד מהם חייב לעבוד
    models = [
        "gemini-1.5-flash",          # הכי חדש
        "gemini-1.5-flash-latest",   # גרסה חלופית
        "gemini-pro"                 # הסוס היציב והוותיק
    ]
    
    last_err = ""
    
    for model in models:
        try:
            # פנייה ישירה ללא ספריות תיווך
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                res_json = json.loads(response.read().decode())
                # אם הגענו לפה - הצלחנו!
                return res_json['candidates'][0]['content']['parts'][0]['text']
                
        except Exception as e:
            last_err = str(e)
            continue # נסה את המודל הבא ברשימה
            
    return f"שגיאה בכל הניסיונות. הודעה אחרונה: {last_err}"

# ==========================================
# 2. צייד הקבצים (מזהה גם סיומות כפולות)
# ==========================================
def find_pdf(base_dir, prefix):
    if not os.path.exists(base_dir): return None
    for f in os.listdir(base_dir):
        if f.lower().startswith(prefix.lower()) and ".pdf" in f.lower():
            return os.path.join(base_dir, f)
    return None

# ==========================================
# 3. ממשק משתמש
# ==========================================
with st.sidebar:
    st.header("🛡️ Database Radar")
    comp = st.selectbox("חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # זיהוי תיקייה (Data/data)
    root = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(root): root = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"
    
    path_fin = find_pdf(f"{root}/Financial_Reports", f"{comp}_{q}_{year}")
    path_sol = find_pdf(f"{root}/Solvency_Reports", f"Solvency_{comp}_{q}_{year}")
    
    st.write(f"📄 דוח כספי: {'✅' if path_fin else '❌'}")
    st.write(f"🛡️ דוח סולבנסי: {'✅' if path_sol else '❌'}")

st.title(f"🏛️ {comp} | Strategic AI Terminal")
t1, t2 = st.tabs(["📊 KPI Dashboard", "🤖 AI Analyst"])

with t2:
    st.subheader("ניתוח דוחות (Direct Bypass Mode)")
    mode = st.radio("בחר דוח:", ["כספי", "סולבנסי"])
    active = path_fin if mode == "כספי" else path_sol
    
    if active:
        st.success(f"קובץ נבחר: {os.path.basename(active)}")
        query = st.text_input("שאל את האנליסט (למשל: מהו ההון העצמי?):")
        
        if st.button("🚀 הרץ ניתוח") and query:
            with st.spinner("מבצע סריקה במודול עוקף תקלות..."):
                try:
                    doc = fitz.open(active)
                    text = "".join([page.get_text() for page in doc[:40]])
                    
                    prompt = f"ניתוח דוח {mode} של {comp}. שאלה: {query}\n\nטקסט:\n{text[:25000]}"
                    
                    # שימוש בפונקציה החדשה
                    ans = ask_google_direct(prompt)
                    
                    st.markdown("---")
                    st.write(ans)
                except Exception as e:
                    st.error(f"תקלה בקובץ: {e}")
    else:
        st.warning("לא נמצא קובץ בתיקייה.")
