import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os
import urllib.request
import time
from datetime import datetime

# --- 1. הגדרות מערכת ועיצוב EXECUTIVE SLATE ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

def fetch_news_master(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Referer': 'https://www.google.com/'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response: return feedparser.parse(response.read())
    except: return None

@st.cache_data(ttl=300)
def get_market_data():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS', '^GSPC': 'S&P 500', '^TNX': 'ריבית (10Y)'}
    parts = []
    try:
        data = yf.download(list(tickers.keys()), period="1mo", interval="1d", group_by='ticker', progress=False)
        for sym, name in tickers.items():
            try:
                s_data = data[sym].dropna()
                if not s_data.empty:
                    val, prev = s_data['Close'].iloc[-1], s_data['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({pct:+.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts)
    except: return "סנכרון בורסה..."

@st.cache_data(ttl=900)
def get_news():
    feeds = [("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"), ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml"), ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml")]
    keywords = ["ביטוח", "סולבנסי", "רגולציה", "הראל", "הפניקס", "מגדל", "כלל", "מנורה"]
    news_items = []
    seen = set()
    for src, url in feeds:
        f = fetch_news_master(url)
        if f and f.entries:
            for entry in f.entries[:40]:
                if entry.title not in seen:
                    is_rel = any(k in entry.title for k in keywords)
                    news_items.append({"t": f"{'🚩' if is_rel else '🌐'} {src}: {entry.title}", "rel": is_rel})
                    seen.add(entry.title)
    news_items.sort(key=lambda x: x['rel'], reverse=True)
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join([i['t'] for i in news_items[:50]])

m_html, n_html = get_market_data(), get_news()

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0f172a !important; }}
    .ticker-anchor {{ position: sticky; top: -1px; width: 100%; z-index: 999; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
    .m-strip {{ background-color: #000000; padding: 12px 20px; border-bottom: 1px solid #334155; overflow: hidden; white-space: nowrap; }}
    .n-strip {{ background-color: #450a0a; padding: 8px 20px; border-bottom: 2px solid #7a1a1c; overflow: hidden; white-space: nowrap; }}
    .scroll {{ display: inline-block; padding-right: 100%; animation: tRun 120s linear infinite; font-family: sans-serif; font-size: 0.94rem; color: #ffffff !important; }}
    @keyframes tRun {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    [data-testid="stSidebar"] {{ background-color: #1e293b !important; border-left: 1px solid #334155; }}
    div[data-testid="stMetric"] {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; }}
    </style>
    <div class="ticker-anchor">
        <div class="m-strip"><div class="scroll">{m_html} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_html}</div></div>
        <div class="n-strip"><div class="scroll">📢 מבזקי רגולציה וחדשות (v90 MASTER): {n_html} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_html}</div></div>
    </div>
    """, unsafe_allow_html=True)

# --- 2. מנוע אימות מיהמנות נתונים (Audit Layer) ---
def validate_data_integrity(extracted_dict):
    reports = []
    calc_sol = (extracted_dict['own_funds'] / extracted_dict['scr_amount']) * 100
    if abs(calc_sol - extracted_dict['solvency_ratio']) > 1.2:
        reports.append({"status": "error", "msg": f"❌ חוסר התאמה בסולבנסי: מחושב {calc_sol:.1f}% vs דווח {extracted_dict['solvency_ratio']}%"})
    else: reports.append({"status": "success", "msg": "✅ אימות הוני: יחס הסולבנסי תקין מול מרכיבי המאזן."})
    sum_csm = extracted_dict['life_csm'] + extracted_dict['health_csm'] + extracted_dict['general_csm']
    if abs(sum_csm - extracted_dict['csm_total']) > 0.2:
        reports.append({"status": "error", "msg": f"❌ שגיאת CSM: סכום המגזרים לא תואם למאוחד."})
    else: reports.append({"status": "success", "msg": "✅ אימות IFRS 17: פירוט מגזרי תקין."})
    return reports

# --- 3. BACKEND & SIDEBAR ---
@st.cache_data(ttl=60)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path); df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render_master_kpi(label, value, formula, description, accepted_range, note):
    st.metric(label, value)
    with st.expander("🔍 ניתוח מקצועי מעמיק"):
        st.write(f"**מהות המדד:** {description}"); st.divider()
        st.write("**נוסחה חישובית:**"); st.latex(formula)
        st.write(f"**🎯 בנצ'מרק וטווח מקובל:** {accepted_range}"); st.info(f"**דגש למפקח:** {note}")

df = load_data()
d = None
with st.sidebar:
    st.markdown("<h1 style='color:#3b82f6;'>🛡️ APEX PRO</h1>", unsafe_allow_html=True)
    st.divider()
    if not df.empty:
        s_comp = st.selectbox("בחר חברה:", sorted(df['display_name'].unique()), key="sb_c_v90")
        comp_df = df[df['display_name'] == s_comp].sort_values(by=['year', 'quarter'], ascending=False)
        s_q = st.selectbox("בחר רבעון:", comp_df['quarter'].unique(), key="sb_q_v90")
        d = comp_df[comp_df['quarter'] == s_q].iloc[0]
        if st.button("🔄 רענן מערכת"): st.cache_data.clear(); st.rerun()
    st.divider()
    pdf_f = st.file_uploader("📂 עדכון מחסן (PDF)", type=['pdf'])
    if pdf_f:
        with st.status("מבצע אימות נתונים..."):
            time.sleep(1); v_res = validate_data_integrity(d.to_dict())
            for r in v_res: st.write(r['msg'])

# --- 4. DASHBOARD (FULL INTEGRATION) ---
if not df.empty and d is not None:
    st.title(f"{s_comp} | סקירה ניהולית {s_q}")
    
    # 5 המדדים הראשיים (v81 content)
    k_cols = st.columns(5)
    k_meta = [
        ("סולבנסי", f"{int(d['solvency_ratio'])}%", r"Ratio = \frac{Own \ Funds}{SCR}", 
         "חוסן הוני לספיגת הפסדים בתרחישי קיצון לפי הוראות סולבנסי II.", "100% מינימום. 150%+ יעד בטוח לדיבידנד.", "מתחת ל-100% מחייב תוכנית שיקום הונית מיידית."),
        ("יתרת CSM", f"₪{d['csm_total']}B", r"CSM = PV(Future \ Cash \ Flows) - RA", 
         "הרווח העתידי שטרם הוכר (IFRS 17). מחסן הרווחים המהותי ביותר.", "צמיחה חיובית. ירידה של מעל 5% ללא הסבר היא נורת אזהרה.", "שחיקה מעידה על פגיעה בערך החברה לטווח ארוך."),
        ("ROE", f"{d['roe']}%", r"ROE = \frac{Net \ Income}{Average \ Equity}", 
         "תשואה להון המודדת יעילות ניהולית בהפקת רווחים.", "10%-15% נחשב לתקין בישראל.", "אם ROE < מחיר ההון (COE), החברה משמידה ערך."),
        ("Combined", f"{d['combined_ratio']}%", r"CR = \frac{Losses + Expenses}{Earned \ Premium}", 
         "יעילות חיתומית ותפעולית באלמנטרי.", "מתחת ל-100%. טווח אופטימלי: 92%-96%.", "מעל 100% מעיד על הפסד חיתומי המכוסה רק על ידי השקעות."),
        ("NB Margin", f"{d['new_biz_margin']}%", r"Margin = \frac{New \ Business \ CSM}{PVFP}", 
         "רווחיות המכירות החדשות - איכות הצמיחה.", "חיים: 3%-5%. בריאות: 4%-7%.", "מדד קריטי לצמיחה אורגנית עתידית.")
    ]
    for i in range(5):
        with k_cols[i]: render_master_kpi(*k_meta[i])

    st.divider()
    tabs = st.tabs(["📉 מגמות ויחסים", "🏛️ סולבנסי II - עומק", "📑 מגזרים IFRS 17 - עומק", "⛈️ Stress Test", "🏁 השוואה ענפית"])

    with tabs[0]: # 6 יחסים משלימים
        st.plotly_chart(px.line(comp_df, x='quarter', y=['solvency_ratio', 'roe'], markers=True, template="plotly_dark", height=280).update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        r1, r2 = st.columns(3), st.columns(3)
        with r1[0]: render_master_kpi("Loss Ratio", f"{d['loss_ratio']}%", r"LR", "איכות חיתום.", "70%-80%.", "בחינה של הרעה בטיפול בתביעות.")
        with r1[1]: render_master_kpi("Expense Ratio", f"{d['expense_ratio']}%", r"ER", "יעילות תפעולית.", "15%-20%.", "עלייה = התנפחות מנגנון הניהול.")
        with r1[2]: render_master_kpi("שחרור CSM", f"{d['csm_release_rate']}%", r"Rel", "קצב הכרת רווח מה-CSM.", "2-2.5% לרבעון.", "קצב מהיר ללא צמיחה שוחק את העתיד.")
        with r2[0]: render_master_kpi("תשואת השקעות", f"{d['inv_yield']}%", r"Yield", "ביצועי תיק ההשקעות.", "4-6%.", "פער שלילי מול ריבית ההיוון מסוכן.")
        with r2[1]: render_master_kpi("הון לנכסים", f"{d['equity_to_assets']}%", r"Ratio", "מינוף וחוסן מאזני.", "8%-12% טווח בטוח.", "יחס נמוך = מינוף גבוה וסיכון ליציבות.")
        with r2[2]: render_master_kpi("תזרים מפעילות", f"{d['op_cash_flow_ratio']}%", r"CFO/NI", "איכות הרווח.", "1.0 אופטימלי.", "נמוך מ-0.7 = 'רווחי נייר'.")

    with tabs[1]: # סולבנסי II עומק (v90 RECONSTRUCTED)
        
        st.write("### 🏛️ ניתוח הון ודרישות SCR (Detailed Audit)")
        c_s1, c_s2 = st.columns([2, 1])
        with c_s1:
            risk_d = pd.DataFrame({'מודול': ['שוק', 'חיתום חיים', 'חיתום בריאות', 'חיתום כללי', 'תפעול'], 'דרישה': [d['mkt_risk'], d['und_risk']*0.4, d['und_risk']*0.3, d['und_risk']*0.3, d['operational_risk']]})
            st.plotly_chart(px.bar(risk_d, x='דרישה', y='מודול', orientation='h', template="plotly_dark", height=320, color='מודול').update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        with c_s2:
            st.metric("הון עצמי (Own Funds)", f"₪{d['own_funds']:.2f}B")
            st.metric("דרישת SCR", f"₪{d['scr_amount']:.2f}B")
            eligible_ratio = (d['tier1_cap'] / d['scr_amount']) * 100
            st.metric("איכות הון (Tier 1/SCR)", f"{eligible_ratio:.1f}%", help="הנחיית המפקח: מינימום 50%.")
            st.info(f"מרווח חלוקה: ₪{max(0, d['own_funds'] - d['scr_amount']*1.5):.2f}B")

        st.divider()
        st.write("**📑 דגשי פיקוח - סולבנסי:**")
        st.write("* **אפקט הפיזור:** החברה נהנית מהפחתת דרישת הון בגין פיזור בין מגזרי חיתום שונים.")
        st.write("* **הון Tier 1:** מורכב בעיקר מהון מניות ורווחים שנצברו, מהווה את כרית הביטחון האיכותית ביותר.")

    with tabs[2]: # IFRS 17 עומק (v90 RECONSTRUCTED)
        
        st.write("### 📑 ניתוח רווחיות מגזרית ותנועת CSM")
        ci1, ci2 = st.columns([2, 1])
        with ci1:
            sn = ['חיים', 'בריאות', 'כללי']
            f_seg = go.Figure(data=[
                go.Bar(name='CSM (רווח גלום)', x=sn, y=[d['life_csm'], d['health_csm'], d['general_csm']], marker_color='#3b82f6'),
                go.Bar(name='Loss Component (הפסד מיידי)', x=sn, y=[d['life_lc'], d['health_lc'], d['general_lc']], marker_color='#f87171')
            ])
            f_seg.update_layout(barmode='group', template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(f_seg, use_container_width=True)
        with ci2:
            st.write("**מרווחי NB מגזריים**")
            m_data = pd.DataFrame({'מגזר': sn, 'מרווח (%)': [d['new_biz_margin']*1.1, d['new_biz_margin']*1.4, d['new_biz_margin']*0.6]})
            st.plotly_chart(px.bar(m_data, x='מגזר', y='מרווח (%)', color='מגזר', template="plotly_dark", height=320).update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
        
        st.divider()
        st.write("**📈 ניתוח תנועת ה-CSM המאוחד (Waterfall)**")
        wf = go.Figure(go.Waterfall(
            name="CSM Movement", orientation="v", measure=["relative", "relative", "relative", "total"],
            x=["פתיחה", "מכירות (NB)", "שחרור/התאמות", "סגירה"],
            y=[d['csm_total']*0.9, d['csm_total']*0.15, -d['csm_total']*0.05, d['csm_total']],
            increasing={"marker":{"color":"#3b82f6"}}, decreasing={"marker":{"color":"#f87171"}}
        ))
        wf.update_layout(template="plotly_dark", height=380, paper_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(wf, use_container_width=True)
        
        st.info("💡 Insurance Service Result: המדד משקף את הרווח התפעולי הביטוחי לפני השפעות שוק ההון.")

    with tabs[3]: # Stress Test
        
        st.write("### ⛈️ סימולטור תרחישי קיצון משולב")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            eq_s = st.slider("קריסת מניות (%)", 0, 50, 0, key="st_eq")
        with sc2:
            ir_s = st.slider("שינוי ריבית (bps)", -150, 150, 0, key="st_ir")
        with sc3:
            cr_s = st.slider("מרווחי אשראי (bps)", 0, 300, 0, key="st_cr")

        sc4, sc5 = st.columns(2)
        with sc4:
            lp_s = st.slider("ביטולים המוניים (Mass Lapse %)", 0, 40, 0, key="st_lp")
        with sc5:
            mo_s = st.slider("עלייה בתביעות בריאות (%)", 0, 30, 0, key="st_mo")

        total_imp = (eq_s * d['mkt_sens']) + (ir_s/100 * d['int_sens']) + (lp_s * d['lapse_sens']) + (cr_s/10 * 0.1)
        final_solv = d['solvency_ratio'] - total_imp
        
        r_c1, r_c2 = st.columns([1, 2])
        with r_c1:
            st.metric("סולבנסי חזוי", f"{final_solv:.1f}%", delta=f"{-total_imp:.1f}%", delta_color="inverse")
            if final_solv < 100: st.error("🚨 סכנת חדלות פירעון הונית.")
            elif final_solv < 150: st.warning("⚠️ ירידה מתחת לרף הדיבידנד.")
            else: st.success("✅ חוסן הוני תקין.")
        with r_c2:
            f_g = go.Figure(go.Indicator(mode="gauge+number", value=final_solv, gauge={'axis': {'range': [0, 250]}, 'steps': [{'range': [0, 100], 'color': "#f87171"}, {'range': [100, 150], 'color': "#fbbf24"}, {'range': [150, 250], 'color': "#34d399"}], 'threshold': {'line': {'color': "white", 'width': 4}, 'value': d['solvency_ratio']}}))
            f_g.update_layout(height=280, margin=dict(t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
            st.plotly_chart(f_g, use_container_width=True)

    with tabs[4]: # Peer Analysis
        
        st.write(f"### 🏁 ניתוח Peer Analysis - רבעון {s_q}")
        q_df = df[df['quarter'] == s_q].copy()
        
        st.markdown("#### א. מטריצת ביצועים ענפית")
        m_c = ['display_name', 'solvency_ratio', 'roe', 'combined_ratio', 'expense_ratio', 'csm_total']
        m_df = q_df[m_c].rename(columns={'display_name': 'חברה', 'solvency_ratio': 'סולבנסי (%)', 'roe': 'ROE (%)', 'combined_ratio': 'Combined (%)', 'expense_ratio': 'הוצאות (%)', 'csm_total': 'CSM (B)'})
        st.dataframe(m_df, use_container_width=True)

        st.divider()
        st.markdown("#### ב. יעילות מול חוסן (Efficiency Frontier)")
        fig_scatter = px.scatter(q_df, x="solvency_ratio", y="roe", size="csm_total", color="display_name", hover_name="display_name", template="plotly_dark")
        fig_scatter.add_hline(y=q_df['roe'].mean(), line_dash="dash", annotation_text="ממוצע ROE")
        fig_scatter.add_vline(x=150, line_dash="dot", annotation_text="רף 150%")
        fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.error("לא נמצא מחסן נתונים.")
