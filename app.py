import os
import streamlit as st
import fitz  # PyMuPDF
import json
import urllib.request
import urllib.error

# ==========================================
# 1. הגדרות מערכת
# ==========================================
st.set_page_config(page_title="MY AI APP", layout="wide")

# ==========================================
# 2. מנוע AI חכם (מתאים גרסאות למודלים)
# ==========================================
def ask_ai_universal(prompt):
    """מנסה מודלים שונים עם כתובות API מותאמות אישית לכל אחד"""
    if "GEMINI_API_KEY" not in st.secrets:
        return "Error: חסר מפתח API ב-Secrets."
    
    api_key = st.secrets["GEMINI_API_KEY"].strip()
    
    # מיפוי מודלים לגרסאות ה-API המתאימות להם
    # Flash חייב v1beta, Pro חייב v1
    model_configs = [
        ("gemini-1.5-flash", "v1beta"),
        ("gemini-1.5-flash-latest", "v1beta"),
        ("gemini-pro", "v1") 
    ]
    
    last_log = []
    
    for model_name, version in model_configs:
        try:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{model_name}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            data = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}]
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                res_json = json.loads(response.read().decode())
                # הצלחה!
                return res_json['candidates'][0]['content']['parts'][0]['text']
                
        except urllib.error.HTTPError as e:
            last_log.append(f"{model_name} ({version}): {e.code}")
            continue
        except Exception as e:
            last_log.append(f"{model_name}: {str(e)}")
            continue
            
    return f"כל המודלים נכשלו. לוג שגיאות: {', '.join(last_log)}"

# ==========================================
# 3. איתור קבצים
# ==========================================
def find_pdf_file(base_dir, file_start_name):
    if not os.path.exists(base_dir): return None
    for f in os.listdir(base_dir):
        if f.lower().startswith(file_start_name.lower()) and ".pdf" in f.lower():
            return os.path.join(base_dir, f)
    return None

# ==========================================
# 4. תפריט צד
# ==========================================
with st.sidebar:
    st.header("🗄️ Database")
    comp = st.selectbox("חברה:", ["Phoenix", "Harel", "Menora", "Clal", "Migdal"])
    year = st.selectbox("שנה:", [2024, 2025, 2026])
    q = st.select_slider("רבעון:", options=["Q1", "Q2", "Q3", "Q4"])
    
    # כפתור דיאגנוסטיקה
    if st.button("בדיקת חיבור למודלים"):
        with st.spinner("בודק תקשורת..."):
            res = ask_ai_universal("בדיקה")
            if "נכשלו" in res or "Error" in res:
                st.error(res)
            else:
                st.success("✅ החיבור תקין! המערכת מצאה מודל זמין.")

    st.divider()
    
    root_path = f"data/Insurance_Warehouse/{comp}/{year}/{q}"
    if not os.path.exists(root_path):
        root_path = f"Data/Insurance_Warehouse/{comp}/{year}/{q}"
    
    fin_path = find_pdf_file(f"{root_path}/Financial_Reports", f"{comp}_{q}_{year}")
    sol_path = find_pdf_file(f"{root_path}/Solvency_Reports", f"Solvency_{comp}_{q}_{year}")
    
    st.write(f"📄 דוח כספי: {'✅' if fin_path else '❌'}")
    st.write(f"🛡️ דוח סולבנסי: {'✅' if sol_path else '❌'}")

# ==========================================
# 5. מסך ראשי
# ==========================================
st.title("MY AI APP 🤖")
st.caption(f"מחובר לקובץ נתונים: {comp} | {year}")

t1, t2 = st.tabs(["📊 מדדים", "💬 צ'אט עם הדוחות"])

with t1:
    st.info("כאן יוצגו המדדים הגרפיים.")

with t2:
    mode = st.radio("בחר קובץ:", ["דוח כספי", "דוח סולבנסי"], horizontal=True)
    active_file = fin_path if mode == "דוח כספי" else sol_path
    
    if active_file:
        st.success(f"מנתח את: {os.path.basename(active_file)}")
        
        query = st.text_input("שאל את ה-AI:")
        
        if st.button("🚀 הרץ ניתוח") and query:
            with st.spinner("סורק דוחות..."):
                try:
                    doc = fitz.open(active_file)
                    text_content = ""
                    # קריאת 40 עמודים ראשונים
                    for i in range(min(len(doc), 40)):
                        text_content += doc[i].get_text()
                    
                    final_prompt = f"""
                    אתה אנליסט מומחה. ענה על השאלה לפי הטקסט.
                    שאלה: {query}
                    טקסט:
                    {text_content[:30000]}
                    """
                    
                    answer = ask_ai_universal(final_prompt)
                    
                    st.markdown("---")
                    if "נכשלו" in answer or "Error" in answer:
                        st.error(answer)
                    else:
                        st.write(answer)
                        
                except Exception as e:
                    st.error(f"תקלה בקובץ: {e}")
    else:
        st.warning("⚠️ לא נמצא קובץ מתאים בתיקייה שנבחרה. אנא בדוק ב-GitHub.")
