import os
import streamlit as st
import fitz  # PyMuPDF
import json
import urllib.request
import urllib.error

# ==========================================
# 1. הגדרות האפליקציה: MY AI APP
# ==========================================
st.set_page_config(page_title="MY AI APP", layout="wide")

# ==========================================
# 2. מנוע AI (חיבור ישיר - עוקף תקלות)
# ==========================================
def ask_ai(prompt):
    """שולח שאלה למודל Gemini 1.5 Flash באמצעות חיבור ישיר"""
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: חסר מפתח API ב-Secrets."
    
    # ניקוי רווחים קריטי
    api_key = st.secrets["GEMINI_API_KEY"].strip()
    
    # כתובת המודל היציב
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode('utf-8')
    
    try:
        # שליחת בקשת רשת רגילה
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            res_json = json.loads(response.read().decode())
            return res_json['candidates'][0]['content']['parts'][0]['text']
            
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return "⛔ שגיאת הרשאה (403): המפתח החדש עדיין לא נקלט. בצע Reboot לאפליקציה."
        return f"שגיאת תקשורת ({e.code}): {e.reason}"
    except Exception as e:
        return f"תקלה כללית: {str(e)}"

# ==========================================
# 3. מנוע איתור קבצים חכם
# ==========================================
def find_pdf_file(base_dir, file_start_name):
    """מוצא קובץ PDF גם אם הסיומת כפולה"""
    if not os.path.exists(base_dir):
        return None
        
    for f in os.listdir(base_dir):
        if f.lower().startswith(file_start_name.lower()) and ".pdf" in f.lower():
            return os.path.join(base_dir, f)
    return None

# ==========================================
# 4. תפריט צד (Sidebar)
# ==========================================
with st.sidebar:
    st.header("🗄️ Database")
    
    comp = st.selectbox("חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    st.divider()
    
    # איתור נתיבים
    root_path = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(root_path):
        root_path = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"
    
    fin_path = find_pdf_file(f"{root_path}/Financial_Reports", f"{comp}_{q}_{year}")
    sol_path = find_pdf_file(f"{root_path}/Solvency_Reports", f"Solvency_{comp}_{q}_{year}")
    
    st.write(f"📄 דוח כספי: {'✅' if fin_path else '❌'}")
    st.write(f"🛡️ דוח סולבנסי: {'✅' if sol_path else '❌'}")

# ==========================================
# 5. מסך ראשי: MY AI APP
# ==========================================
st.title("MY AI APP 🤖")
st.caption(f"מערכת אנליזה מתקדמת: {comp} | {year} {q}")

t1, t2 = st.tabs(["📊 מדדים", "💬 צ'אט עם הדוחות"])

with t1:
    st.info("כאן יוצגו המדדים הגרפיים (Solvency, ROE, CSM).")

with t2:
    mode = st.radio("בחר קובץ לניתוח:", ["דוח כספי", "דוח סולבנסי"], horizontal=True)
    active_file = fin_path if mode == "דוח כספי" else sol_path
    
    if active_file:
        st.success(f"מחובר לקובץ: {os.path.basename(active_file)}")
        
        query = st.text_input("מה תרצה לדעת? (למשל: מהו ההון העצמי?)")
        
        if st.button("🚀 שאל את ה-AI") and query:
            with st.spinner("ה-AI סורק את הדוח..."):
                try:
                    doc = fitz.open(active_file)
                    text_content = ""
                    for i in range(min(len(doc), 50)):
                        text_content += doc[i].get_text()
                    
                    final_prompt = f"""
                    אתה אנליסט מומחה. ענה על השאלה לפי הטקסט המצורף.
                    שאלה: {query}
                    טקסט מהדוח:
                    {text_content[:30000]}
                    """
                    
                    answer = ask_ai(final_prompt)
                    
                    st.markdown("---")
                    if "שגיאה" in answer:
                        st.error(answer)
                    else:
                        st.write(answer)
                        
                except Exception as e:
                    st.error(f"תקלה בקובץ: {e}")
    else:
        st.warning("⚠️ לא נמצא קובץ מתאים בתיקייה שנבחרה. אנא בדוק ב-GitHub.")
