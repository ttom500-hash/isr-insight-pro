import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import feedparser
import os
from datetime import datetime

# --- 1. הגדרות מערכת וסרגלים כפולים (v53.0 FIXED SYNTAX) ---
st.set_page_config(page_title="Apex Executive Command", page_icon="🛡️", layout="wide")

# פונקציה חסינה למשיכת מדדי שוק
@st.cache_data(ttl=600)
def get_market_ticker():
    tickers = {'^TA125.TA': 'ת"א 125', 'ILS=X': 'USD/ILS', 'EURILS=X': 'EUR/ILS', '^GSPC': 'S&P 500', '^TNX': 'ריבית (10Y)'}
    parts = []
    try:
        for sym, name in tickers.items():
            try:
                t = yf.Ticker(sym)
                hist = t.history(period="2d")
                if not hist.empty:
                    val = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    pct = ((val / prev) - 1) * 100
                    clr = "#4ade80" if pct >= 0 else "#f87171"
                    arr = "▲" if pct >= 0 else "▼"
                    parts.append(f'<span style="color:white; font-weight:bold;">{name}:</span> <span style="color:{clr};">{val:.2f} ({arr}{pct:.2f}%)</span>')
            except: continue
        return " &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; ".join(parts) if parts else "טוען מדדי שוק..."
    except: return "מתחבר לבורסה..."

# מנוע חדשות רגולטורי מורחב
@st.cache_data(ttl=1800)
def get_regulatory_news():
    feeds = [
        ("גלובס", "https://www.globes.co.il/webservice/rss/rss.aspx?did=585"),
        ("TheMarker", "https://www.themarker.com/misc/rss-feeds.xml"),
        ("כלכליסט", "https://www.calcalist.co.il/GeneralRSS/0,16335,L-8,00.xml")
    ]
    keywords = ["ביטוח", "פנסיה", "גמל", "סולבנסי", "ריבית", "אינפלציה", "שוק ההון", "אג\"ח", "חיתום", "CSM", "IFRS", "דיבידנד", "רגולציה", "רשות שוק ההון"]
    news_parts = []
    seen = set()
    for src, url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:30]:
                if any(k in entry.title for k in keywords) and entry.title not in seen:
                    news_parts.append(f"🚩 {src}: {entry.title}")
                    seen.add(entry.title)
        except: continue
    return " &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; ".join(news_parts) if news_parts else "ממתין לעדכוני רגולציה..."

m_content = get_market_ticker()
n_content = get_regulatory_news()

# CSS - הגנה על חלון החיפוש, מניעת חפיפה וביטול expand_more
st.markdown(f"""
    <style>
    .stApp {{ background-color: #020617 !important; }}
    
    /* סרגלים בראש הדף */
    .ticker-header {{ position: fixed; top: 0; left: 0; width: 100%; z-index: 9999; background-color: #0f172a; }}
    .m-line {{ background-color: #0f172a; padding: 10px 0; border-bottom: 1px solid #1e293b; overflow: hidden; }}
    .n-line {{ background-color: #450a0a; padding: 7px 0; overflow: hidden; border-bottom: 2px solid #7a1a1c; }}
    
    .scroll-text {{
        display: inline-block; padding-right: 100%; animation: tScroll 60s linear infinite;
        font-family: sans-serif; font-size: 0.9rem; white-space: nowrap; color: #ffffff !important;
    }}
    @keyframes tScroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-100%); }} }}
    .body-spacer {{ margin-top: 115px; }}

    /* Sidebar (חלון החיפוש והגרירה) - שכבה עליונה */
    [data-testid="stSidebar"] {{ background-color: #0f172a !important; z-index: 100000 !important; border-left: 1px solid #1e293b; }}
    [data-testid="stExpanderChevron"], i, svg {{ font-family: 'Material Icons' !important; text-transform: none !important; }}
    
    html, body, .stMarkdown p, label {{ color: #ffffff !important; }}
    div[data-testid="stMetric"] {{ background: #0d1117; border: 1px solid #1e293b; border-radius: 8px; padding: 12px !important; }}
    div[data-testid="stMetricValue"] {{ color: #3b82f6 !important; font-weight: 700 !important; font-size: 1.6rem !important; }}
    
    /* חלון גרירת קבצים */
    [data-testid="stFileUploadDropzone"] {{ background-color: #111827 !important; border: 2px dashed #3b82f6 !important; }}
    </style>
    
    <div class="ticker-header">
        <div class="m-line"><div class="scroll-text">{m_content} &nbsp;&nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp;&nbsp; {m_content}</div></div>
        <div class="n-line"><div class="scroll-text">🚨 מבזקי רגולציה ושוק: {n_content} &nbsp;&nbsp;&nbsp;&nbsp; ● &nbsp;&nbsp;&nbsp;&nbsp; {n_content}</div></div>
    </div>
    <div class="body-spacer"></div>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ---
@st.cache_data(ttl=60)
def load_data():
    path = 'data/database.csv'
    if not os.path.exists(path): return pd.DataFrame()
    df = pd.read_csv(path); df.columns = df.columns.str.strip()
    df['display_name'] = df['company'].apply(lambda x: str(x).split('_')[0])
    for col in df.columns.drop(['company', 'quarter', 'display_name']):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def render
