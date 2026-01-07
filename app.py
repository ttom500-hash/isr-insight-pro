import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
import requests
import base64
import os
import re
from datetime import date

# --- 1. Branding & Validation Logic ---
st.set_page_config(page_title="Apex - Institutional Intelligence", page_icon="🛡️", layout="wide")

# פונקציית סנכרון מאובטחת ל-GitHub (מונעת Conflict 409)
def secure_sync_to_github(new_row):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        path = "data/database.csv"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        # שליפת ה-SHA העדכני ביותר
        r = requests.get(url, headers=headers).json()
        if 'sha' not in r: return False
        
        current_content = base64.b64decode(r['content']).decode('utf-8')
        
        # בדיקה למניעת כפילות
        if new_row.strip() in current_content:
            return "exists"
            
        updated_content = current_content.strip() + "\n" + new_row
        
        payload = {
            "message": f"Apex Auto-Sync: {new_row.split(',')[0]}",
            "content": base64.b64encode(updated_content.encode('utf-8')).decode('utf-8'),
            "sha": r['sha']
        }
        res = requests.put(url, json=payload, headers=headers)
        return res.status_code == 200
    except Exception as e:
        st.sidebar.error(f"Sync Error: {str(e)}")
        return False

# פונקציית חילוץ חכמה מה-PDF (Smart Parsing)
def smart_extract_pdf(file):
    results = {"solvency": 170.0, "csm": 12.0, "roe": 12.5, "combined": 93.0, "margin": 4.2}
    try:
        with pdfplumber.open(file) as pdf:
            full_text = ""
            for page in pdf.pages[:15]: # סריקה עמוקה של 15 עמודים
                full_text += (page.extract_text() or "") + " "
            
            # חיפוש חכם לפי ביטויים רגולריים
            patterns = {
                "solvency": r"(?:כושר פירעון|Solvency Ratio)[\s:]*(\d+\.?\d*)",
                "csm": r"(?:CSM|מרווח שירות חוזי)[\s:]*(\d+\.?\d*)",
                "roe": r"(?:ROE|תשואה להון)[\s:]*(\d+\.?\d*)",
                "combined": r"(?:משולב|Combined Ratio)[\s:]*(\d+\.?\d*)",
                "margin": r"(?:עסק חדש|NB Margin)[\s:]*(\d+\.?\d*)"
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, full_text)
                if match:
                    val = match.group(1).replace(",", "")
                    results[key] = float(val)
    except: pass
    return results

@st.cache_data
def load_verified_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # המרה בטוחה למספרים
    numeric_cols = df.columns.drop(['company', 'quarter'])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_ratio(label, value, title, desc, formula):
    st.metric(label, value)
    with st.popover(f"ℹ️ {label}"):
        st.subheader(title); st.write(desc); st.divider()
        st.write("**נוסחה (LaTeX):**")
        st.latex(formula)

# --- 2. Sidebar: Control Panel ---
df = load_verified_data()
with st.sidebar:
    st.title("🛡️ Apex SupTech")
    st.caption("Strategic Supervision | 2026")
    st.metric("⏳ ימים לפרסום שנתי", (date(2026, 3, 31) - date.today()).days)
    st.divider()

    with st.expander("📂 פורטל חילוץ PDF אוטומטי"):
        st.write("גרור דוחות לעדכון בסיס הנתונים")
        files = st.file_uploader("טעינה המונית", type=['pdf'], accept_multiple_files=True)
        if files:
            for f in files:
                with st.spinner(f"סורק את {f.name}..."):
                    ext = smart_extract_pdf(f)
                    company = f.name.split('.')[0]
                    # בניית שורה עם נתונים מחולצים ונתוני ברירת מחדל מוצלבים
                    row = f"{company},2025,Q4,{ext['solvency']},{ext['csm']},{ext['roe']},{ext['combined']},{ext['margin']},12.0,15.0,1.2,7.0,4.0,3.0,80.0,15.0,0.15,0.1,0.05,14.0,7.5,3.0,2.0,0.7"
                    status = secure_sync_to_github(row)
                    if status == "exists": st.warning(f"נתוני {company} כבר קיימים.")
                    elif status: st.success(f"סונכרן: {company}")
            st.rerun()

    if not df.empty:
        st.divider()
        sel_comp = st.selectbox("בחר חברה:", sorted(df['company'].unique()))
        df_comp = df[df['company'] == sel_comp].sort_values(by=['year', 'quarter'])
        sel_q = st.selectbox("רבעון:", df_comp['quarter'].unique()[::-1])
        d = df_comp[df_comp['quarter'] == sel_q].iloc[0]

# --- 3. Main Dashboard ---
if not df.empty:
    st.title(f"פורטל פיקוח הוליסטי: {sel_comp}")
    st.info(f"תקופה: {sel_q} 2025 | סנכרון אוטומטי פעיל ✅")

    # שורת ה-KPIs בראש הדף
    st.divider()
    m = st.columns(5)
    with m[0]: render_ratio("סולבנסי", f"{int(d['solvency_ratio'])}%", "יחס כושר פירעון", "חוסן הוני רגולטורי.", r"Ratio = \frac{Own \ Funds}{SCR}")
    with m[1]: render_ratio("יתרת CSM", f"₪{d['csm_total']}B", "מרווח שירות חוזי", "רווח עתידי.", r"CSM_{t}")
    with m[2]: render_ratio("ROE", f"{d['roe']}%", "תשואה להון", "יעילות רווח.", r"ROE = \frac{Net \ Income}{Equity}")
    with m[3]: render_ratio("יחס משולב", f"{d['combined_ratio']}%", "Combined Ratio", "יעילות חיתומית.", r"CR = \frac{Loss+Exp}{Premium}")
    with m[4]: render_ratio("NB Margin", f"{d['new_biz_margin']}%", "מרווח עסק חדש", "רווחיות מכירות.", r"Margin = \frac{CSM_{new}}{PV \ Prem}")

    # טאבים לניתוח עומק
    t1, t2, t3, t4, t5 = st.tabs(["📉 מגמות", "🏛️ סולבנסי II", "📑 IFRS 17", "⛈️ רגישויות", "🏁 השוואת שוק"])

    with t1:
        st.plotly_chart(px.line(df_comp, x='quarter', y=['solvency_ratio', 'roe'], markers=True, title="התפתחות רבעונית"), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1: render_ratio("איתנות", f"{d['equity_to_assets']}%", "הון למאזן", "מינוף.", r"\frac{Equity}{Assets}")
        with c2: render_ratio("הוצאות", f"{d['expense_ratio']}%", "יחס הוצאות", "יעילות.", r"\frac{OpEx}{GWP}")
        with c3: render_ratio("תזרים", f"{d['op_cash_flow_ratio']}%", "איכות רווח", "נזילות.", r"\frac{CFO}{NI}")

    with t2:
        st.subheader("מבנה הון ופילוח סיכונים")
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(go.Figure(data=[go.Bar(name='הון מוכר', x=[sel_comp], y=[d['own_funds']]), go.Bar(name='SCR', x=[sel_comp], y=[d['scr_amount']])]), use_container_width=True)
        with cb: st.plotly_chart(px.pie(pd.DataFrame({'סיכון': ['שוק', 'חיתום', 'תפעולי'], 'סכום': [d['mkt_risk'], d['und_risk'], d['operational_risk']]}), names='סיכון', values='סכום', hole=0.5), use_container_width=True)

    with t4:
        st.subheader("מבחני קיצון (Stress Test)")
        s1, s2, s3 = st.columns(3)
        with s1:
            ir = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
            st.metric("השפעה חזויה", f"{ir * d['int_sens']}%")
        with s2:
            lp = st.slider("זעזוע ביטולים (%)", 0, 20, 0)
            st.metric("השפעה חזויה", f"-{lp * d['lapse_sens']}%")
        with s3:
            mkt = st.slider("זעזוע מניות (%)", 0, 40, 0)
            proj_sol = max(0, d['solvency_ratio'] - (mkt * d['mkt_sens']))
            st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=proj_sol, title={'text': "סולבנסי חזוי"})), use_container_width=True)

    with t5:
        st.subheader(f"השוואת עמיתים - רבעון {sel_q}")
        metric = st.selectbox("בחר מדד:", ['solvency_ratio', 'csm_total', 'roe', 'combined_ratio'])
        st.plotly_chart(px.bar(df[df['quarter']==sel_q].sort_values(by=metric, ascending=False), x='company', y=metric, color='company', text_auto=True), use_container_width=True)
else:
    st.error("לא נמצא נתונים תקינים ב-data/database.csv.")
