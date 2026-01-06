import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime
import io

# ==========================================
# 1. עיצוב FINTECH PRO (קריאות מקסימלית)
# ==========================================
st.set_page_config(page_title="ISR-TITAN PRO", layout="wide", page_icon="🏦")

def load_pro_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700&display=swap');
        
        :root {
            --bg-main: #0f172a;       /* Slate 900 */
            --bg-card: #1e293b;       /* Slate 800 */
            --text-main: #f8fafc;     /* Slate 50 */
            --text-sub: #cbd5e1;      /* Slate 300 */
            --accent: #38bdf8;        /* Sky 400 */
            --success: #34d399;       /* Emerald 400 */
            --danger: #fb7185;        /* Rose 400 */
            --border: #334155;        /* Slate 700 */
        }
        
        .stApp {
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: 'Heebo', sans-serif;
            direction: rtl;
        }
        
        /* טיפוגרפיה */
        h1, h2, h3, h4 {
            color: var(--text-main) !important;
            font-weight: 700;
            text-align: right;
            margin-bottom: 0.5rem;
        }
        
        p, div, label, span, li {
            color: var(--text-sub);
            text-align: right;
            font-size: 1rem;
        }
        
        /* כרטיסי KPI */
        .kpi-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-right: 4px solid var(--accent);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: var(--text-sub);
        }
        
        .kpi-label {
            font-size: 0.9rem;
            color: var(--text-sub);
            font-weight: 500;
            margin-bottom: 8px;
            display: block;
        }
        
        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-main);
            display: block;
        }
        
        .kpi-badge {
            font-size: 0.75rem;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            display: inline-block;
            margin-top: 8px;
        }

        /* טבלאות */
        div[data-testid="stDataFrame"] {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
        }
        div[data-testid="stDataFrame"] * {
            color: var(--text-sub) !important;
        }

        /* סרגל צד */
        section[data-testid="stSidebar"] {
            background-color: #020617;
            border-left: 1px solid var(--border);
        }
        
        /* כפתור ייצוא */
        .stDownloadButton button {
            background-color: var(--bg-card);
            color: var(--accent);
            border: 1px solid var(--accent);
        }
        .stDownloadButton button:hover {
            background-color: var(--accent);
            color: var(--bg-main);
        }
        
        /* סליידרים וטאבים */
        .stSlider > div > div > div > div { background-color: var(--accent); }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-sub);
            border-radius: 6px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: var(--accent);
            color: #0f172a !important;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

load_pro_css()

# =================================
