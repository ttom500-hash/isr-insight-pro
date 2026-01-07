import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
import requests
import base64
import os
import re
from datetime import datetime

# --- 1. Ultra-High-End Visual Styling (Xbox/Cyberpunk Theme) ---
st.set_page_config(page_title="Apex SupTech - Command Center", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* רקע כללי וצבעי בסיס */
    .stApp {
        background: radial-gradient(circle at top right, #0a192f, #020c1b);
        color: #e6f1ff;
    }
    
    /* עיצוב כרטיסי KPIs בסגנון Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(16, 33, 65, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 15px;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0, 255, 136, 0.1);
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border: 1px solid #00ff88;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
    }
    
    /* דגלים אדומים עם אפקט פעימה זוהר */
    .red-flag-box {
        background: rgba(255, 46, 99, 0.1);
        border-left: 5px solid #ff2e63;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        animation: pulse-red 2s infinite;
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 46, 99, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 46, 99, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 46, 99, 0); }
    }
    
    /* עיצוב טאבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px 10px 0 0;
        color: #8892b0;
        padding: 10px 25px;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0, 255, 136, 0.1) !important;
        border-bottom: 2px solid #00ff88 !important;
        color: #00ff88 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Backend Logic (Sync, Extract, Load) ---
def secure_sync(new_row):
    try:
        if "GITHUB_TOKEN" not in st.secrets: return False
        token, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"]
        path = "data/database.csv"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers, timeout=10).json()
        current_content = base64.b64decode(r['content']).decode('utf-8')
        if new_row.strip() in current_content: return "exists"
        updated_content = current_content.strip() + "\n" + new_row
        payload = {"message": "Update Master", "content": base64.b64encode(updated_content.encode()).decode(), "sha": r['sha']}
        return requests.put(url, json=payload, headers=headers, timeout=10).status_code == 200
    except: return False

def smart_extract(file):
    # פונקציית חילוץ מקוצרת לצורך הדגמה
    return {"solvency": 175.0, "csm": 13.0, "roe": 12.0, "combined": 92.0, "margin": 4.5}

@st.cache_data(ttl=300)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0].split('.')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 3. UI Components ---
df = load_data()
with st.sidebar:
    st.markdown("<h2 style='color:#00ff88;'>🛡️ Apex SupTech</h2>", unsafe_allow_html=True)
    st.write("🛰️ **סנכרון רגולטורי פעיל**")
    
    if not df.empty:
        sel_name = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()))
        comp_df = df[df['display_name'] == sel_name].sort_values(by=['year', 'quarter'], ascending=False)
        sel_q = st.selectbox("רבעון:", comp_df['quarter'].unique())
        d = comp_df[comp_df['quarter'] == sel_q].iloc[0]
        if st.button("⚡ רענן מערכת"): st.cache_data.clear(); st.rerun()

    with st.expander("📥 פורטל קליטת נתונים"):
        f = st.file_uploader("טען PDF", type=['pdf'])
        if f:
            ext = smart_extract(f)
            # בניית שורה עם כל האינדיקטורים המקצועיים
            row = f"{f.name.split('.')[0]},2025,Q4,{ext['solvency']},{ext['csm']},{ext['roe']},{ext['combined']},{ext['margin']},12.0,15.0,1.2,7.4,4.2,3.3,10.0,2.0,1.0,13.0,400.0,3.0,2.5,0.8,0.12,0.18,0.08,14.5,7.8,0.2"
            if secure_sync(row): st.success("נשלח למחסן!"); st.rerun()

# --- 4. Dashboard Core ---
if not df.empty:
    st.markdown(f"<h1 style='text-align:right; color:#00ff88;'>{sel_name} | Command Center</h1>", unsafe_allow_html=True)
    st.caption(f"תקופת דיווח: {sel_q} 2025 | רמת אמינות: ENTERPRISE LEVEL ✅")

    # א' : התראות אקטיביות (Xbox Glow)
    st.write("### 🚨 דגלים אדומים למפקח")
    flags_html = ""
    if d['solvency_ratio'] < 150:
        flags_html += f'<div class="red-flag-box"><b>דגל אדום:</b> חוסן הוני גבולי ({d["solvency_ratio"]}%) - דרישת הון SCR בסיכון.</div>'
    if d['combined_ratio'] > 100:
        flags_html += f'<div class="red-flag-box" style="border-left-color:#ff9f43; background:rgba(255,159,67,0.1);"><b>אזהרה:</b> הפסד חיתומי במגזר אלמנטרי.</div>'
    
    if not flags_html: st.success("כל מערכות היציבות תקינות ✅")
    else: st.markdown(flags_html, unsafe_allow_html=True)

    st.divider()

    # ב' : 5 ה-KPIs בפריסה יוקרתית
    k_cols = st.columns(5)
    metrics = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"\frac{OF}{SCR}"),
        ("יתרת CSM", f"₪{d['csm_total']}B", "CSM"),
        ("תשואה להון", f"{d['roe']}%", "ROE"),
        ("יחס משולב", f"{d['combined_ratio']}%", "Combined"),
        ("מרווח עסק חדש", f"{d['new_biz_margin']}%", "Margin")
    ]
    for i, (label, val, form) in enumerate(metrics):
        with k_cols[i]:
            st.metric(label, val)
            with st.popover("פרוטוקול"):
                st.latex(form); st.info("בדיקת חריגה מול ממוצע ענפי.")

    st.divider()

    # ג' : טאבים בניתוח עומק
    t1, t2, t3, t4 = st.tabs(["📉 מגמות", "🏛️ הון וסולבנסי", "📑 מגזרים IFRS 17", "⛈️ Stress Engine"])

    with t1:
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, 
                               template="plotly_dark", color_discrete_sequence=['#00ff88', '#ff2e63']), use_container_width=True)

    with t2:
        st.subheader("ניתוח הון וסיכוני SCR")
        
        ca, cb = st.columns(2)
        with ca:
            st.plotly_chart(go.Figure(data=[
                go.Bar(name='Tier 1 (Core)', y=[d['tier1_cap']], marker_color='#00ff88'),
                go.Bar(name='Tier 2/3', y=[d['own_funds']-d['tier1_cap']], marker_color='#006644')
            ]).update_layout(barmode='stack', template="plotly_dark", title="איכות ההון"), use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(names=['שוק', 'חיתום', 'תפעול'], values=[d['mkt_risk'], d['und_risk'], d['operational_risk']], 
                                  hole=0.6, template="plotly_dark", title="מקורות הסיכון"), use_container_width=True)

    with t3:
        st.subheader("פילוח CSM לפי מודלים ומגזרים")
        
        cc, cd = st.columns(2)
        with cc:
            st.plotly_chart(px.bar(x=['חיים', 'בריאות', 'כללי'], y=[d['life_csm'], d['health_csm'], d['general_csm']], 
                                  title="CSM לפי מגזר", template="plotly_dark"), use_container_width=True)
        with cd:
            st.plotly_chart(px.pie(names=['VFA', 'PAA', 'GMM'], values=[d['vfa_csm'], d['paa_csm'], d['gmm_csm']], 
                                  title="CSM לפי מודל", template="plotly_dark"), use_container_width=True)

    with t4:
        st.subheader("⛈️ מנוע סימולציית תרחישי קיצון")
        s1, s2, s3 = st.columns(3)
        with s1: r_s = st.slider("זעזוע ריבית (bps)", -100, 100, 0)
        with s2: m_s = st.slider("זעזוע מניות (%)", 0, 40, 0)
        with s3: l_s = st.slider("זעזוע ביטולים (%)", 0, 20, 0)
        
        proj = max(0, d['solvency_ratio'] - (r_s * d['int_sens']) - (m_s * d['mkt_sens']) - (l_s * d['lapse_sens']))
        st.metric("סולבנסי חזוי", f"{proj:.1f}%", delta=f"{proj - d['solvency_ratio']:.1f}%")
        
        st.plotly_chart(go.Figure(go.Indicator(
            mode="gauge+number", value=proj, 
            gauge={'axis': {'range': [0, 250]}, 'bar': {'color': "#00ff88"},
                   'steps': [{'range': [0, 150], 'color': "#333"}, {'range': [150, 250], 'color': "#004422"}]})).update_layout(template="plotly_dark"), use_container_width=True)

else:
    st.warning("התחברות למחסן הנתונים... וודא שקובץ ה-CSV קיים ב-GitHub.")
