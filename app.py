import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# Set page configuration
st.set_page_config(page_title="Regulator Pro Dashboard", layout="wide", page_icon="🛡️")

def load_css():
    st.markdown("""
        <style>
        /* Dark Background */
        .stApp {
            background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
            color: white;
        }
        
        /* Glassmorphism Cards */
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        div[data-testid="metric-container"]:hover {
            transform: scale(1.02);
            border-color: #00ff96;
        }
        
        /* Metric Text Coloring */
        div[data-testid="metric-container"] label {
            color: #e0e0e0 !important;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            text-shadow: 0 0 10px rgba(255,255,255,0.3);
        }

        /* Pulse Animation */
        @keyframes pulse-animation {
            0% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(0, 255, 150, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 255, 150, 0); }
        }
        .pulse-icon {
            width: 12px;
            height: 12px;
            background-color: #00ff96;
            border-radius: 50%;
            display: inline-block;
            animation: pulse-animation 2s infinite;
            margin-right: 8px;
        }

        /* Headers */
        h1, h2, h3 {
            font-family: 'Helvetica Neue', sans-serif;
            color: #ffffff !important;
            text-shadow: 0 0 15px rgba(0,255,150,0.4);
        }
        
        /* Slider Color */
        .stSlider > div > div > div > div {
            background-color: #00ff96;
        }
        
        /* Alerts */
        .stAlert {
            background-color: rgba(255, 75, 75, 0.1);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 75, 75, 0.3);
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

# --- Data Engine (Simulation) ---
@st.cache_data
def get_insurance_data():
    # Simulated IFRS 17 Data
    data = {
        "הפניקס": {
            "CSM": 14500, "CSM_New": 1200, "CSM_Release": -900, 
            "Loss_Component": 50, "SCR_Ratio": 118, "Equity": 9500, 
            "Risk_Adj": 800, "Segment": "General & Life"
        },
        "הראל": {
            "CSM": 13200, "CSM_New": 1100, "CSM_Release": -850, 
            "Loss_Component": 120, "SCR_Ratio": 112, "Equity": 8800, 
            "Risk_Adj": 750, "Segment": "Health Focus"
        },
        "מגדל": {
            "CSM": 16000, "CSM_New": 900, "CSM_Release": -1100, 
            "Loss_Component": 450, "SCR_Ratio": 104, "Equity": 7200, 
            "Risk_Adj": 1200, "Segment": "Life Heavy"
        },
        "כלל": {
            "CSM": 11500, "CSM_New": 950, "CSM_Release": -800, 
            "Loss_Component": 200, "SCR_Ratio": 109, "Equity": 6500, 
            "Risk_Adj": 600, "Segment": "General"
        },
        "מנורה": {
            "CSM": 12800, "CSM_New": 1300, "CSM_Release": -820, 
            "Loss_Component": 0, "SCR_Ratio": 125, "Equity": 7800, 
            "Risk_Adj": 500, "Segment": "General & Pension"
        }
    }
    return pd.DataFrame(data).T

df_original = get_insurance_data()

# --- Sidebar: Stress Test Simulator ---
st.sidebar.markdown("## ⚙️ Stress Test Simulator")
st.sidebar.info("Adjust sliders to test solvency sensitivity:")

equity_shock = st.sidebar.slider("📉 Equity Market Drop (%)", 0, 40, 0)
interest_shock = st.sidebar.slider("🏦 Interest Rate Shift (bps)", -100, 100, 0)
longevity_shock = st.sidebar.slider("👴 Longevity Increase (%)", 0, 10, 0)

# Logic to recalculate SCR based on stress
def apply_stress(row):
    # Calculate Equity Hit
    equity_hit_factor = row['Equity'] * 0.005 
    equity_impact = equity_shock * equity_hit_factor / 100
    
    # Calculate Liability Impact
    rate_impact = (interest_shock * -0.15) 
    longevity_impact = (longevity_shock * 0.8)
    
    # New Ratio
    current_ratio = row['SCR_Ratio']
    shock_effect = (equity_impact / 100) + rate_impact + longevity_impact
    new_scr_req = current_ratio - shock_effect
    
    return round(new_scr_req, 2)

df = df_original.copy()
df['Stressed_SCR'] = df.apply(apply_stress, axis=1)

# --- Main Dashboard UI ---

# Header with Pulse Icon
col_h1, col_h2 = st.columns([0.8, 0.2])
with col_h1:
    st.title("Insurance Regulator Pro")
    st.caption("Advanced IFRS 17 & Solvency II Monitoring System")
with col_h2:
    st.markdown('<div style="text-align: left; margin-top: 30px;"><span class="pulse-icon"></span><span style="color:#00ff96; font-weight:bold; font-size:14px;">Live Data</span></div>', unsafe_allow_html=True)

st.markdown("---")

# Search Bar
search_term = st.text_input("🔍 Search Company or Segment...", "")
if search_term:
    df = df[df.index.str.contains(search_term, na=False) | df['Segment'].str.contains(search_term, na=False)]

if df.empty:
    st.warning(f"No results found for '{search_term}'.")
else:
    # --- IFRS 17 Analysis ---
    st.subheader("📊 IFRS 1
