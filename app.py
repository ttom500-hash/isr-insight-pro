import os
import streamlit as st
import fitz  # PyMuPDF
import json
import urllib.request
import urllib.error

st.set_page_config(page_title="Apex Pro Enterprise", layout="wide")

# ==========================================
# 1. מנוע איתור מודלים אוטומטי (הפתרון מחוץ לקופסא)
# ==========================================
def get_working_model(api_key):
    """שואל את גוגל אילו מודלים זמינים למפתח הזה ומחזיר את הטוב ביותר"""
    try:
        # בדיקה אקטיבית: רשימת המודלים הזמינים לחשבון שלך
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
            # חיפוש מודל שתומך ביצירת תוכן (generateContent)
            for m in data.get('models', []):
                name = m['name'] # למשל: models/gemini-1.5-flash
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    # העדפה ל-Flash או Pro
                    if 'flash' in name or 'pro' in name:
                        return name.replace("models/", "")
            
            # אם לא מצאנו העדפה, נחזיר את הראשון שקיים
            if data.get('models'):
                return data['models'][0]['name'].replace("models/", "")
                
    except Exception as e:
        return None # המפתח כנראה לא תקין או חסום
    return None

def ask_google_dynamic(prompt):
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: חסר מפתח API"
    
    # ניקוי המפתח
    api_key = st.secrets["GEMINI_API_KEY"].strip()
    
    # --- שלב הקסם: מציאת מודל שעובד ---
    valid_model = get_working_model(api_key)
    
    if not valid_model:
        return "שגיאה קריטית: המפתח שלך לא מאפשר גישה לאף מודל. ייתכן שצריך להנפיק מפתח חדש ב-Google AI Studio."
    
    # שימוש במודל שנמצא
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{valid_model}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode())
            return res_json['candidates'][0]['content']['parts'][0]['text']
            
    except urllib.error.HTTPError as e:
        return f"שגיאה במודל {valid_model}: {e.code} {e.reason}"
    except Exception as e:
        return f"שגיאה כללית: {str(e)}"

# ==========================================
# 2. צייד הקבצים
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
    
    root = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(root): root = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"
    
    path_fin = find_pdf(f"{root}/Financial_Reports", f"{comp}_{q}_{year}")
    path_sol = find_pdf(f"{root}/Solvency_Reports", f"Solvency_{comp}_{q}_{year}")
    
    st.write(f"📄 דוח כספי: {'✅' if path_fin else '❌'}")
    st.write(f"🛡️ דוח סולבנסי: {'✅' if path_sol else '❌'}")

st.title(f"🏛️ {comp} | Strategic AI Terminal")
t1, t2 = st.tabs(["📊 KPI Dashboard", "🤖 AI Analyst"])

with t2:
    st.subheader("ניתוח דוחות (Dynamic Mode)")
    mode = st.radio("בחר דוח:", ["כספי", "סולבנסי"])
    active = path_fin if mode == "כספי" else path_sol
    
    if active:
        st.success(f"קובץ בטיפול: {os.path.basename(active)}")
        query = st.text_input("שאל את האנליסט (למשל: מהו ההון העצמי?):")
        
        if st.button("🚀 הרץ ניתוח") and query:
            with st.spinner("מאתר מודל זמין ומבצע ניתוח..."):
                try:
                    doc = fitz.open(active)
                    text = "".join([page.get_text() for page in doc[:40]])
                    
                    prompt = f"ניתוח דוח {mode} של {comp}. שאלה: {query}\n\nטקסט:\n{text[:25000]}"
                    
                    ans = ask_google_dynamic(prompt)
                    
                    st.markdown("---")
                    if "שגיאה" in ans:
                        st.error(ans)
                        st.info("💡 המלצה: גש ל-aistudio.google.com והנפק מפתח חדש בחינם.")
                    else:
                        st.success(ans)
                except Exception as e:
                    st.error(f"תקלה בקובץ: {e}")
    else:
        st.warning("לא נמצא קובץ בתיקייה.")
