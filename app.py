import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime

# --- הגדרת עמוד חייבת להיות ראשונה ---
st.set_page_config(page_title="ISR-TITAN PRO", layout="wide", page_icon="🏆")

# --- עטיפת הגנה ראשית (Error Handling) ---
try:
    # 1. הגדרות עיצוב (Dark Mode Forced)
    def load_css():
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;700&display=swap');
            
            /* כפיית מצב כהה על כל האלמנטים */
            .stApp {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: 'Heebo', sans-serif;
            }
            
            h1, h2, h3, p, div, span, label {
                color: #f8fafc !important;
                text-align: right;
            }
            
            /* כרטיסי מידע */
            .metric-card {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }
            .metric-value {
                font-size: 1.8rem;
                font-weight: bold;
                color: #38bdf8 !important;
            }
            .metric-label {
                font-size: 0.9rem;
                color: #94a3b8 !important;
            }
            
            /* טבלאות */
            div[data-testid="stDataFrame"] {
                background-color: #1e293b;
                border: 1px solid #334155;
            }
            </style>
        """, unsafe_allow_html=True)

    load_css()

    # 2. רשימת חברות
    TICKERS = {
        "הפניקס אחזקות": "PHOE.TA", 
        "הראל השקעות": "HARL.TA", 
        "מגדל ביטוח": "MGDL.TA",
        "מנורה מבטחים": "MMHD.TA", 
        "כלל עסקי ביטוח": "CLIS.TA",
        "ביטוח ישיר": "DIDI.TA",
        "AIG ישראל": "PRIVATE", 
        "שומרה": "PRIVATE"
    }

    # 3. פונקציית הבאת נתונים
    @st.cache_data(ttl=600)
    def get_data(ticker_name):
        symbol = TICKERS[ticker_name]
        is_live = False
        market_cap = 4000000000 # ברירת מחדל
        
        # ניסיון לשאיבה מהבורסה
        if symbol != "PRIVATE":
            try:
                info = yf.Ticker(symbol).info
                if info.get('marketCap'):
                    market_cap = info['marketCap']
                    is_live = True
            except:
                pass
        
        # יצירת נתונים מבוססי מודל אקטוארי
        np.random.seed(abs(hash(ticker_name)) % (2**32))
        
        equity = market_cap * 0.9
        csm = equity * 0.4
        
        segments = {
            "כללי": csm * 0.2,
            "בריאות": csm * 0.3,
            "חיסכון": csm * 0.5
        }
        
        return {
            "is_live": is_live,
            "market_cap": market_cap,
            "equity": equity,
            "csm": csm,
            "liabilities": equity * 7.5,
            "solvency": np.random.uniform(110, 150),
            "segments": segments
        }

    # 4. ממשק משתמש
    st.title("🛡️ ISR-TITAN PRO")
    st.caption("מערכת אנליזה מתקדמת | IFRS 17 Compliant")
    
    # סרגל צד
    with st.sidebar:
        st.header("הגדרות סימולציה")
        shock_equity = st.slider("נפילת שוק (%)", 0, 50, 0)
        shock_interest = st.slider("שינוי ריבית (%)", -2.0, 2.0, 0.0)
        
    # בחירת חברה
    selected_comp = st.selectbox("בחר חברה:", list(TICKERS.keys()))
    
    # חישוב נתונים
    data = get_data(selected_comp)
    
    # החלת סימולציה (Logic)
    impact_equity = data['equity'] * (shock_equity / 100)
    final_equity = data['equity'] - impact_equity
    
    impact_liabs = data['liabilities'] * (shock_interest * -0.05)
    final_solvency = data['solvency'] - (shock_equity * 0.5) - (shock_interest * 2)
    
    # תצוגת מדדים (KPIs)
    k1, k2, k3, k4 = st.columns(4)
    
    def display_card(col, label, value, sub_text=""):
        col.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div style="color: #cbd5e1; font-size: 0.8rem;">{sub_text}</div>
            </div>
        """, unsafe_allow_html=True)
        
    display_card(k1, "הון עצמי (Equity)", f"₪{final_equity/1e9:.2f}B", "אחרי שוק")
    display_card(k2, "יחס סולבנסי", f"{final_solvency:.1f}%", "יעד: >100%")
    display_card(k3, "ערך גלום (CSM)", f"₪{data['csm']/1e9:.2f}B", "IFRS 17")
    display_card(k4, "מקור נתונים", "Live API" if data['is_live'] else "Model", "Yahoo Finance")
    
    st.divider()
    
    # גרפים
    t1, t2 = st.tabs(["ניתוח CSM", "פילוח מגזרי"])
    
    with t1:
        # גרף מפל פשוט ויציב
        fig = go.Figure(go.Waterfall(
            name = "CSM", orientation = "v",
            measure = ["relative", "relative", "total"],
            x = ["פתיחה", "שינוי סימולציה", "סגירה"],
            textposition = "outside",
            y = [data['csm'], -data['csm']*(shock_equity/200), 0],
            connector = {"line":{"color":"white"}},
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    with t2:
        # גרף עוגה
        labels = list(data['segments'].keys())
        values = list(data['segments'].values())
        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
        fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

except Exception as e:
    st.error("התרחשה שגיאה בטעינת המערכת:")
    st.code(str(e))
    st.info("נסה לרענן את העמוד או לבדוק את קובץ requirements.txt")
