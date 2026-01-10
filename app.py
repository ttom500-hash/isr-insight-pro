import streamlit as st
import pandas as pd
import requests
import base64
import os
import io # הוספה: עבור ייצוא לאקסל
import plotly.express as px
import plotly.graph_objects as go
import json
import time
from datetime import datetime
from jsonschema import validate, ValidationError

# ==============================================================================
# 1. מילון מונחים רגולטורי (The Regulator's Encyclopedia)
# ==============================================================================
DEFINITIONS = {
    # KPIs
    "net_profit": "הרווח הכולל לבעלי המניות (אחרי מס). ירידה חדה עשויה להעיד על אירועים חד פעמיים או שחיקה בחיתום.",
    "total_csm": "Contractual Service Margin: 'מחסנית הרווחים' העתידית. המנוע של IFRS 17.",
    "roe": "תשואה להון עצמי. בנצ'מארק ענפי: 10%-15%.",
    "gross_premiums": "GWP: סך הפרמיות ברוטו. צמיחה מעידה על כוח שוק.",
    "total_assets": "AUM: סך המאזן המאוחד (נכסי נוסטרו + עמיתים).",
    
    # Solvency
    "solvency_ratio": "יחס סולבנסי II. יחס < 100% דורש תוכנית הבראה. יחס < 115% הוא תמרור אזהרה.",
    "scr": "Solvency Capital Requirement: ההון הנדרש לספיגת זעזועים של 1 ל-200 שנה.",
    "tier1_capital": "הון רובד 1 (ליבה): הון מניות ורווחים צבורים. ההון האיכותי ביותר.",
    "tier2_capital": "הון רובד 2 (משני): כתבי התחייבות נדחים ומכשירים מורכבים.",
    
    # Ratios & IFRS 17
    "combined_ratio": "יחס משולב (ביטוח כללי): (תביעות + הוצאות) / פרמיה. מעל 100% = הפסד חיתומי.",
    "loss_ratio": "יחס תביעות (Loss Ratio): מודד את איכות החיתום נטו.",
    "expense_ratio": "יחס הוצאות: יעילות תפעולית ועמלות סוכנים.",
    "lcr": "Liquidity Coverage Ratio: יחס נזילות ל-30 יום.",
    "leverage": "מינוף פיננסי: יחס הון למאזן. מינוף גבוה מעלה סיכון במשבר.",
    "new_business_csm": "CSM עסקים חדשים: הערך הנוכחי של חוזים חדשים שנמכרו.",
    "onerous_contracts": "רכיב הפסד: קבוצות חוזים שבהן ההוצאות עולות על ההכנסות.",
    "real_yield": "תשואה ריאלית על ההשקעות (בניכוי מדד).",
    "unquoted_pct": "שיעור נכסים לא סחירים (Level 3). קשים לשערוך ומימוש."
}

# ==============================================================================
# 2. עיצוב המערכת (Deep Navy Theme)
# ==============================================================================
st.set_page_config(page_title="Apex Regulator Pro", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* רקע ראשי כהה */
    .main { background-color: #0e1117; color: white; }
    
    /* עיצוב כרטיסיות מדדים */
    .stMetric { 
        background-color: #1c2e4a; 
        padding: 15px; 
        border-radius: 8px; 
        border-right: 4px solid #2e7bcf; 
        box-shadow: 3px 3px 10px rgba(0,0,0,0.5); 
        transition: transform 0.2s;
    }
    .stMetric:hover { transform: scale(1.02); }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.6rem; font-family: 'Segoe UI', sans-serif; font-weight: 600; }
    div[data-testid="stMetricLabel"] { color: #b0c4de !important; font-size: 0.9rem; }

    /* טיקר בורסאי */
    .ticker-wrap { 
        background: #000000; 
        color: #00ff00; 
        padding: 12px; 
        font-family: 'Courier New', monospace; 
        border-bottom: 2px solid #2e7bcf; 
        font-size: 1.0rem; 
        white-space: nowrap;
        overflow: hidden;
    }

    /* קופסאות התרעה (Red Flags) */
    .alert-box { 
        padding: 15px; 
        border-radius: 6px; 
        margin-bottom: 15px; 
        font-weight: bold; 
        border: 1px solid; 
        display: flex;
        align-items: center;
    }
    .alert-critical { background-color: #2c0b0e; border-color: #ff4b4b; color: #ff9999; }
    .alert-warning { background-color: #2c250b; border-color: #f0ad4e; color: #f0e68c; }
    
    /* כותרות */
    h1, h2, h3 { color: #e6e6e6; }
    .css-10trblm { color: #2e7bcf; }

    /* Actuary Note Box (תוספת חדשה להערות) */
    .actuary-note {
        background-color: #1e293b;
        border-top: 3px solid #00ff00;
        padding: 15px;
        margin-bottom: 20px;
        color: #dcdcdc;
        font-family: 'Courier New', monospace;
    }
    </style>
""", unsafe_allow_html=True)

# סרגל בורסה
ticker_text = (
    "🌍 מדדים: ת\"א-35: 2,045 ▲ (+0.8%) | ת\"א-ביטוח: 2,540 ▲ (+1.4%) | S&P 500: 5,120 ▲ | "
    "🇮🇱 מניות ביטוח (יומי): הראל (+1.2%) | הפניקס (-0.5%) | מגדל (+0.8%) | כלל (+2.1%) | מנורה (+0.3%) | איילון (0.0%)"
)
st.markdown(f'<div class="ticker-wrap"><marquee scrollamount="10">{ticker_text}</marquee></div>', unsafe_allow_html=True)

# ==============================================================================
# 3. נתוני אמת מורחבים (Q1-Q3 2025) - The Truth Source
# ==============================================================================
FULL_DATA = {
    "Q3 2025": { 
        "Harel": { # תוקן: רווח 634M, תשואה 5.2%
            "core_kpis": { "net_profit": 634.0, "total_csm": 17133.0, "roe": 22.0, "gross_premiums": 3900.0, "total_assets": 167754.0 },
            "ifrs17_segments": { "life_csm": 11532.0, "health_csm": 5601.0, "general_csm": 0.0, "onerous_contracts": 0.0, "new_business_csm": 1265.0, "models": {"PAA": 35, "GMM": 65} },
            "investment_mix": { "govt_bonds_pct": 30.0, "corp_bonds_pct": 20.0, "stocks_pct": 15.0, "real_estate_pct": 10.0, "unquoted_pct": 63.0, "real_yield": 5.2 },
            "financial_ratios": { "loss_ratio": 76.0, "expense_ratio": 19.0, "combined_ratio": 88.0, "lcr": 1.35, "leverage": 6.9, "roa": 1.5, "roi": 5.5 },
            "solvency": { "solvency_ratio": 182.0, "tier1_capital": 13797.0, "tier2_capital": 3500.0, "scr": 9428.0 },
            "consistency_check": { "opening_csm": 16687.0, "new_business_csm": 398.0, "csm_release": 405.0, "closing_csm": 17133.0 },
            "notes": "Q3: רווח כולל חריג לטובה (634M) הנובע מתשואות שוק חזקות (5.2%) ושיערוכים. יציבות ב-CSM וסולבנסי."
        },
        "Phoenix": {
            "core_kpis": { "net_profit": 586.0, "total_csm": 9579.0, "roe": 33.3, "gross_premiums": 2307.0, "total_assets": 169551.0 },
            "ifrs17_segments": { "life_csm": 6636.0, "health_csm": 7719.0, "general_csm": 0.0, "onerous_contracts": 0.0, "new_business_csm": 621.0, "models": {"PAA": 35, "GMM": 65} },
            "investment_mix": { "govt_bonds_pct": 35.0, "corp_bonds_pct": 20.0, "stocks_pct": 14.0, "real_estate_pct": 10.0, "unquoted_pct": 27.3, "real_yield": 7.74 },
            "financial_ratios": { "loss_ratio": 74.0, "expense_ratio": 18.0, "combined_ratio": 84.8, "lcr": 1.4, "leverage": 5.1, "roa": 0.8, "roi": 6.2 },
            "solvency": { "solvency_ratio": 178.0, "tier1_capital": 10287.0, "tier2_capital": 4547.0, "scr": 9191.0 },
            "consistency_check": { "opening_csm": 8837.0, "new_business_csm": 621.0, "csm_release": 761.0, "closing_csm": 9579.0 },
            "notes": "Q3: ביטול הפסדים נוסף (168M). תשואות ריאליות חזקות (7.74%) התורמות משמעותית לרווחיות המשתנה (VFA) ול-CSM."
        },
        "Migdal": {
            "core_kpis": { "net_profit": 535.0, "total_csm": 12500.0, "roe": 24.0, "gross_premiums": 2100.0, "total_assets": 219362.0 },
            "ifrs17_segments": { "life_csm": 6636.0, "health_csm": 6426.0, "general_csm": 0.0, "onerous_contracts": 350.0, "new_business_csm": 795.0, "models": {"PAA": 20, "GMM": 80} },
            "investment_mix": { "govt_bonds_pct": 45.0, "corp_bonds_pct": 20.0, "stocks_pct": 13.0, "real_estate_pct": 8.0, "unquoted_pct": 27.0, "real_yield": 2.0 },
            "financial_ratios": { "loss_ratio": 82.0, "expense_ratio": 20.0, "combined_ratio": 70.8, "lcr": 1.1, "leverage": 3.9, "roa": 0.3, "roi": 3.1 },
            "solvency": { "solvency_ratio": 131.0, "tier1_capital": 12565.0, "tier2_capital": 5744.0, "scr": 13685.0 },
            "consistency_check": { "opening_csm": 12200.0, "new_business_csm": 795.0, "csm_release": 355.0, "closing_csm": 12500.0 },
            "notes": "Q3: שיפור דרמטי ב-Combined Ratio (מ-84% ל-70.8%) המעיד על טיוב חיתומי עמוק. הכרה בחוזים מפסידים בסך 350 מ'."
        },
        "Clal": {
            "core_kpis": { "net_profit": 507.0, "total_csm": 8813.0, "roe": 19.0, "gross_premiums": 7200.0, "total_assets": 147369.0 },
            "ifrs17_segments": { "life_csm": 4076.0, "health_csm": 4737.0, "general_csm": 0.0, "onerous_contracts": 4.0, "new_business_csm": 120.0, "models": {"PAA": 30, "GMM": 70} },
            "investment_mix": { "govt_bonds_pct": 20.0, "corp_bonds_pct": 12.0, "stocks_pct": 15.0, "real_estate_pct": 10.0, "unquoted_pct": 68.0, "real_yield": 8.34 },
            "financial_ratios": { "loss_ratio": 78.0, "expense_ratio": 19.0, "combined_ratio": 80.0, "lcr": 1.25, "leverage": 4.8, "roa": 0.9, "roi": 5.1 },
            "solvency": { "solvency_ratio": 160.0, "tier1_capital": 10733.0, "tier2_capital": 4828.0, "scr": 10040.0 },
            "consistency_check": { "opening_csm": 9004.0, "new_business_csm": 120.0, "csm_release": 237.0, "closing_csm": 8813.0 },
            "notes": "Q3: הרעה ב-Combined Ratio (80%). שחיקה ברווחיות החיתומית. תשואה גבוהה במשתתפות."
        },
        "Menora": {
            "core_kpis": { "net_profit": 425.0, "total_csm": 7900.0, "roe": 42.7, "gross_premiums": 1861.0, "total_assets": 62680.0 },
            "ifrs17_segments": { "life_csm": 2500.0, "health_csm": 4300.0, "general_csm": 0.0, "onerous_contracts": 0.0, "new_business_csm": 300.0, "models": {"PAA": 40, "GMM": 60} },
            "investment_mix": { "govt_bonds_pct": 40.0, "corp_bonds_pct": 25.0, "stocks_pct": 19.0, "real_estate_pct": 10.0, "unquoted_pct": 16.0, "real_yield": 10.92 },
            "financial_ratios": { "loss_ratio": 75.0, "expense_ratio": 19.0, "combined_ratio": 78.7, "lcr": 1.45, "leverage": 13.1, "roa": 1.9, "roi": 6.8 },
            "solvency": { "solvency_ratio": 181.0, "tier1_capital": 7567.0, "tier2_capital": 2200.0, "scr": 6019.0 },
            "consistency_check": { "opening_csm": 7600.0, "new_business_csm": 300.0, "csm_release": 200.0, "closing_csm": 7900.0 },
            "notes": "Q3: זינוק בסולבנסי ל-181% עקב גיוס 800 מיליון ש\"ח אג\"ח (סדרה י'). מובילת התשואות (10.92%). איתות חיובי בתיק הסיעוד."
        }
    },
    "Q2 2025": {
        "Harel": { "core_kpis": {"net_profit": 364, "total_csm": 16687, "roe": 14.8, "gross_premiums": 4300, "total_assets": 162048}, "ifrs17_segments": {"life_csm": 11400, "health_csm": 5287, "new_business_csm": 458, "onerous_contracts": 0, "models": {"PAA": 35, "GMM": 65}}, "investment_mix": {"govt_bonds_pct": 30, "corp_bonds_pct": 20, "stocks_pct": 15, "real_estate_pct": 10, "unquoted_pct": 63, "real_yield": 3.4}, "financial_ratios": {"loss_ratio": 76, "expense_ratio": 19, "combined_ratio": 78.6, "lcr": 1.3, "leverage": 6.9, "roa": 1.2, "roi": 3.8}, "solvency": {"solvency_ratio": 182, "tier1_capital": 11507, "tier2_capital": 5266, "scr": 9754}, "consistency_check": {"opening_csm": 16538, "new_business_csm": 458, "csm_release": 415, "closing_csm": 16687}, "notes": "Q2: זינוק בסולבנסי עקב גיוס אג\"ח." },
        "Phoenix": { "core_kpis": {"net_profit": 780, "total_csm": 8837, "roe": 27.0, "gross_premiums": 3561, "total_assets": 169551}, "ifrs17_segments": {"life_csm": 6400, "health_csm": 7500, "new_business_csm": 527, "onerous_contracts": 0, "models": {"PAA": 35, "GMM": 65}}, "investment_mix": {"govt_bonds_pct": 35, "corp_bonds_pct": 20, "stocks_pct": 14, "real_estate_pct": 10, "unquoted_pct": 27.4, "real_yield": 6.14}, "financial_ratios": {"loss_ratio": 74, "expense_ratio": 18, "combined_ratio": 71.2, "lcr": 1.4, "leverage": 5.1, "roa": 0.9, "roi": 5.8}, "solvency": {"solvency_ratio": 178, "tier1_capital": 10287, "tier2_capital": 4547, "scr": 9191}, "consistency_check": {"opening_csm": 8600, "new_business_csm": 527, "csm_release": 483, "closing_csm": 8837}, "notes": "Q2: ביטול הפסדים (הכנסה) בסך 150M." },
        "Migdal": { "core_kpis": {"net_profit": 551, "total_csm": 12200, "roe": 27.4, "gross_premiums": 7700, "total_assets": 212533}, "ifrs17_segments": {"life_csm": 11500, "health_csm": 700, "new_business_csm": 300, "onerous_contracts": 0, "models": {"PAA": 20, "GMM": 80}}, "investment_mix": {"govt_bonds_pct": 45, "corp_bonds_pct": 20, "stocks_pct": 13, "real_estate_pct": 8, "unquoted_pct": 27, "real_yield": -1.1}, "financial_ratios": {"loss_ratio": 82, "expense_ratio": 20, "combined_ratio": 80.0, "lcr": 1.1, "leverage": 3.9, "roa": 0.3, "roi": 2.1}, "solvency": {"solvency_ratio": 131, "tier1_capital": 12565, "tier2_capital": 5744, "scr": 13685}, "consistency_check": {"opening_csm": 12041, "new_business_csm": 300, "csm_release": 320, "closing_csm": 12200}, "notes": "Q2: שיפור בסולבנסי ל-131%." },
        "Clal": { "core_kpis": {"net_profit": 555, "total_csm": 9004, "roe": 18.0, "gross_premiums": 6900, "total_assets": 146398}, "ifrs17_segments": {"life_csm": 4100, "health_csm": 4800, "new_business_csm": 95, "onerous_contracts": 1, "models": {"PAA": 30, "GMM": 70}}, "investment_mix": {"govt_bonds_pct": 20, "corp_bonds_pct": 12, "stocks_pct": 15, "real_estate_pct": 10, "unquoted_pct": 68, "real_yield": 5.2}, "financial_ratios": {"loss_ratio": 78, "expense_ratio": 19, "combined_ratio": 75.6, "lcr": 1.2, "leverage": 4.8, "roa": 0.9, "roi": 4.1}, "solvency": {"solvency_ratio": 160, "tier1_capital": 10733, "tier2_capital": 4828, "scr": 10040}, "consistency_check": {"opening_csm": 10465, "new_business_csm": 95, "csm_release": 209, "closing_csm": 9004}, "notes": "Q2: שחיקה ברווחיות חיתומית." },
        "Menora": { "core_kpis": {"net_profit": 444, "total_csm": 7600, "roe": 23.9, "gross_premiums": 1861, "total_assets": 60810}, "ifrs17_segments": {"life_csm": 2100, "health_csm": 4900, "new_business_csm": 200, "onerous_contracts": 0, "models": {"PAA": 40, "GMM": 60}}, "investment_mix": {"govt_bonds_pct": 40, "corp_bonds_pct": 25, "stocks_pct": 19, "real_estate_pct": 10, "unquoted_pct": 16, "real_yield": 6.17}, "financial_ratios": {"loss_ratio": 75, "expense_ratio": 19, "combined_ratio": 78.7, "lcr": 1.45, "leverage": 13.0, "roa": 1.9, "roi": 5.5}, "solvency": {"solvency_ratio": 163.6, "tier1_capital": 5742, "tier2_capital": 2144, "scr": 4821}, "consistency_check": {"opening_csm": 7700, "new_business_csm": 200, "csm_release": 190, "closing_csm": 7600}, "notes": "Q2: רווחיות חיתומית בריאה." }
    },
    "Q1 2025": {
        "Harel": { "core_kpis": {"net_profit": 264, "total_csm": 16538, "roe": 12.0, "gross_premiums": 3900, "total_assets": 158662}, "ifrs17_segments": {"life_csm": 10900, "health_csm": 5538, "new_business_csm": 409, "onerous_contracts": 0, "models": {"PAA": 35, "GMM": 65}}, "investment_mix": {"govt_bonds_pct": 30, "corp_bonds_pct": 20, "stocks_pct": 15, "real_estate_pct": 10, "unquoted_pct": 63, "real_yield": 1.2}, "financial_ratios": {"loss_ratio": 76, "expense_ratio": 19, "combined_ratio": 96.0, "lcr": 1.3, "leverage": 6.8, "roa": 1.2, "roi": 3.2}, "solvency": {"solvency_ratio": 159, "tier1_capital": 11507, "tier2_capital": 5266, "scr": 9754}, "consistency_check": {"opening_csm": 16100, "new_business_csm": 409, "csm_release": 400, "closing_csm": 16538}, "notes": "Q1: יחס סולבנסי בסיסי. אין אירועים חריגים ב-CSM." },
        "Phoenix": { "core_kpis": {"net_profit": 1837, "total_csm": 4500, "roe": 15.0, "gross_premiums": 3410, "total_assets": 160739}, "ifrs17_segments": {"life_csm": 2200, "health_csm": 2300, "new_business_csm": 354, "onerous_contracts": 0, "models": {"PAA": 35, "GMM": 65}}, "investment_mix": {"govt_bonds_pct": 35, "corp_bonds_pct": 20, "stocks_pct": 14, "real_estate_pct": 10, "unquoted_pct": 30, "real_yield": 4.34}, "financial_ratios": {"loss_ratio": 74, "expense_ratio": 18, "combined_ratio": 71.2, "lcr": 1.4, "leverage": 5.1, "roa": 0.8, "roi": 4.8}, "solvency": {"solvency_ratio": 181, "tier1_capital": 10177, "tier2_capital": 3680, "scr": 8434}, "consistency_check": {"opening_csm": 4300, "new_business_csm": 354, "csm_release": 292, "closing_csm": 4500}, "notes": "Q1: רווח חריג מאוד ב-Q1 עקב חלוקת דיבידנד בעין ושיערוך נכסים." },
        "Migdal": { "core_kpis": {"net_profit": 254, "total_csm": 12041, "roe": 12.7, "gross_premiums": 7700, "total_assets": 225593}, "ifrs17_segments": {"life_csm": 11000, "health_csm": 1041, "new_business_csm": 150, "onerous_contracts": 0, "models": {"PAA": 20, "GMM": 80}}, "investment_mix": {"govt_bonds_pct": 45, "corp_bonds_pct": 20, "stocks_pct": 13, "real_estate_pct": 8, "unquoted_pct": 27, "real_yield": -1.4}, "financial_ratios": {"loss_ratio": 82, "expense_ratio": 20, "combined_ratio": 84.8, "lcr": 1.1, "leverage": 4.2, "roa": 0.3, "roi": 1.2}, "solvency": {"solvency_ratio": 123, "tier1_capital": 11508, "tier2_capital": 5638, "scr": 13416}, "consistency_check": {"opening_csm": 11900, "new_business_csm": 150, "csm_release": 300, "closing_csm": 12041}, "notes": "Q1: תשואה שלילית בהשקעות. סולבנסי נמוך מהמתחרים." },
        "Clal": { "core_kpis": {"net_profit": 239, "total_csm": 10465, "roe": 15.0, "gross_premiums": 8300, "total_assets": 152306}, "ifrs17_segments": {"life_csm": 4200, "health_csm": 4800, "new_business_csm": 183, "onerous_contracts": 0, "models": {"PAA": 30, "GMM": 70}}, "investment_mix": {"govt_bonds_pct": 20, "corp_bonds_pct": 12, "stocks_pct": 15, "real_estate_pct": 10, "unquoted_pct": 69, "real_yield": 3.0}, "financial_ratios": {"loss_ratio": 78, "expense_ratio": 19, "combined_ratio": 69.4, "lcr": 1.2, "leverage": 5.5, "roa": 0.9, "roi": 3.5}, "solvency": {"solvency_ratio": 158, "tier1_capital": 10388, "tier2_capital": 4674, "scr": 10739}, "consistency_check": {"opening_csm": 10300, "new_business_csm": 183, "csm_release": 192, "closing_csm": 10465}, "notes": "Q1: חשיפה גבוהה ללא סחיר." },
        "Menora": { "core_kpis": {"net_profit": 291, "total_csm": 7700, "roe": 18.0, "gross_premiums": 1681, "total_assets": 58416}, "ifrs17_segments": {"life_csm": 2000, "health_csm": 4700, "new_business_csm": 150, "onerous_contracts": 0, "models": {"PAA": 40, "GMM": 60}}, "investment_mix": {"govt_bonds_pct": 40, "corp_bonds_pct": 25, "stocks_pct": 19, "real_estate_pct": 10, "unquoted_pct": 16, "real_yield": 4.33}, "financial_ratios": {"loss_ratio": 75, "expense_ratio": 19, "combined_ratio": 82.0, "lcr": 1.4, "leverage": 12.0, "roa": 1.9, "roi": 4.6}, "solvency": {"solvency_ratio": 157, "tier1_capital": 5288, "tier2_capital": 2200, "scr": 4473}, "consistency_check": {"opening_csm": 7600, "new_business_csm": 150, "csm_release": 180, "closing_csm": 7700}, "notes": "Q1: תוצאות יציבות." }
    }
}

DEFAULT_MOCK = FULL_DATA["Q3 2025"]["Phoenix"]

# סכמה (Schema) למנוע ה-AI
IFRS17_SCHEMA = {
    "type": "object",
    "required": ["core_kpis", "ifrs17_segments", "investment_mix", "financial_ratios", "solvency", "consistency_check", "meta"],
    "properties": {
        "core_kpis": { "type": "object", "properties": { "net_profit": {"type": ["number", "null"]}, "total_csm": {"type": ["number", "null"]}, "roe": {"type": ["number", "null"]}, "gross_premiums": {"type": ["number", "null"]}, "total_assets": {"type": ["number", "null"]} } },
        "ifrs17_segments": { "type": "object", "properties": { "life_csm": {"type": ["number", "null"]}, "health_csm": {"type": ["number", "null"]}, "general_csm": {"type": ["number", "null"]}, "onerous_contracts": {"type": ["number", "null"]}, "new_business_csm": {"type": ["number", "null"]} } },
        "investment_mix": { "type": "object", "properties": { "govt_bonds_pct": {"type": ["number", "null"]}, "corp_bonds_pct": {"type": ["number", "null"]}, "stocks_pct": {"type": ["number", "null"]}, "real_estate_pct": {"type": ["number", "null"]}, "unquoted_pct": {"type": ["number", "null"]}, "real_yield": {"type": ["number", "null"]} } },
        "financial_ratios": { "type": "object", "properties": { "loss_ratio": {"type": ["number", "null"]}, "combined_ratio": {"type": ["number", "null"]}, "lcr": {"type": ["number", "null"]}, "leverage": {"type": ["number", "null"]}, "roa": {"type": ["number", "null"]} } },
        "solvency": { "type": "object", "properties": { "solvency_ratio": {"type": ["number", "null"]}, "tier1_capital": {"type": ["number", "null"]}, "tier2_capital": {"type": ["number", "null"]}, "scr": {"type": ["number", "null"]} } },
        "consistency_check": { "type": "object", "properties": { "opening_csm": {"type": ["number", "null"]}, "new_business_csm": {"type": ["number", "null"]}, "csm_release": {"type": ["number", "null"]}, "closing_csm": {"type": ["number", "null"]} } },
        "meta": { "type": "object", "properties": { "confidence": {"type": "number"}, "extraction_time": {"type": "string"} } }
    }
}

# ==============================================================================
# 4. מנועי עיבוד ולוגיקה
# ==============================================================================

def get_red_flags(data):
    """מנוע זיהוי חריגות רגולטוריות"""
    flags = []
    # Solvency
    sol = data['solvency']['solvency_ratio']
    if sol < 100: flags.append(("CRITICAL", f"🚨 יחס סולבנסי קריטי: {sol}% (נדרשת תוכנית הבראה)"))
    elif sol < 115: flags.append(("WARNING", f"⚠️ יחס סולבנסי נמוך: {sol}%"))
    
    # IFRS 17
    onerous = data['ifrs17_segments']['onerous_contracts']
    if onerous > 0: flags.append(("WARNING", f"⚠️ זוהו חוזים מפסידים (Onerous): ₪{onerous}M"))
    
    # Investments
    unquoted = data['investment_mix']['unquoted_pct']
    if unquoted > 20: flags.append(("WARNING", f"⚠️ חשיפה חריגה ללא סחיר: {unquoted}%"))
    
    # Profitability
    combined = data['financial_ratios']['combined_ratio']
    if combined > 100: flags.append(("WARNING", f"⚠️ הפסד חיתומי בביטוח כללי (Combined: {combined}%)"))
    
    return flags

def analyze_report(file_path, api_key, retries=3):
    """מנוע AI מוקשח (לשימוש עתידי עם מפתחות API)"""
    if not os.path.exists(file_path): return None, f"קובץ חסר: {file_path}"
    with open(file_path, "rb") as f: pdf_data = base64.b64encode(f.read()).decode('utf-8')
    
    system_prompt = """
    You are an expert Israeli Insurance Regulator. Extract data from Hebrew IFRS 17 reports.
    CRITICAL:
    1. 'total_csm': "יתרת מרווח שירות חוזי".
    2. 'new_business_csm': "תוספת בגין חוזים חדשים".
    3. 'onerous_contracts': "רכיב הפסד".
    4. 'solvency_ratio': Economic ratio ("בתקופת הפריסה").
    5. 'unquoted_pct': Percentage of Level 3 assets ("רמה 3").
    OUTPUT: JSON matching schema. Return null if missing.
    """
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": system_prompt}, {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}]}]}
    
    for attempt in range(retries):
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                raw = response.json()['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(raw.replace('```json', '').replace('```', '').strip())
                data["meta"]["extraction_time"] = datetime.utcnow().isoformat()
                validate(instance=data, schema=IFRS17_SCHEMA)
                return data, "success"
            elif response.status_code in [429, 500]: time.sleep(2**attempt); continue
            else: return None, f"API Error: {response.text}"
        except Exception: time.sleep(1)
    return None, "Connection Failed"

def get_benchmark_data(selected_companies, quarter):
    """מייצר נתוני השוואה דינמיים לפי רבעון"""
    data = {"חברה": [], "Solvency": [], "ROE": [], "CSM": [], "Combined": []}
    for comp in selected_companies:
        comp_data = FULL_DATA[quarter].get(comp, DEFAULT_MOCK)
        data["חברה"].append(comp)
        data["Solvency"].append(comp_data["solvency"]["solvency_ratio"])
        data["ROE"].append(comp_data["core_kpis"]["roe"])
        data["CSM"].append(comp_data["core_kpis"]["total_csm"])
        data["Combined"].append(comp_data["financial_ratios"]["combined_ratio"])
    return pd.DataFrame(data)

def fmt(v, s=""): 
    """פונקציית פירמוט מספרים"""
    return f"{v:,.1f}{s}" if v is not None else "N/A"

# פונקציות הוספה חדשות: ייצוא וגרפים מתקדמים
def generate_excel(company, quarter):
    """ייצוא נתונים לאקסל"""
    d = FULL_DATA[quarter][company]
    df_core = pd.DataFrame([d['core_kpis']])
    df_sol = pd.DataFrame([d['solvency']])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_core.to_excel(writer, sheet_name='Core_KPIs')
        df_sol.to_excel(writer, sheet_name='Solvency')
    return output.getvalue()

def create_waterfall(d):
    """יצירת גרף מפל ל-CSM"""
    c = d['consistency_check']
    start = c.get('opening_csm', 0)
    new_biz = c.get('new_business_csm', 0)
    release = c.get('csm_release', 0)
    end = d['core_kpis']['total_csm']
    
    fig = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["פתיחה", "עסקים חדשים", "שחרור לרווח", "סגירה"],
        textposition = "outside",
        text = [f"{start:,.0f}", f"+{new_biz}", f"-{release}", f"{end:,.0f}"],
        y = [start, new_biz, -release, end],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#ff4b4b"}},
        increasing = {"marker":{"color":"#00ff00"}},
        totals = {"marker":{"color":"#2e7bcf"}}
    ))
    fig.update_layout(title="תנועה ב-CSM (מיליוני ש\"ח)", template="plotly_dark", height=400, showlegend=False)
    return fig

def create_radar_chart(company_data):
    """יצירת תרשים עכביש פרופיל סיכון"""
    categories = ['סולבנסי', 'ROE', 'נזילות (1-לא סחיר)', 'רווחיות (1-CR)', 'תשואה']
    val_c = [
        company_data['solvency']['solvency_ratio']/200, 
        company_data['core_kpis']['roe']/30, 
        (100-company_data['investment_mix']['unquoted_pct'])/100,
        (100-(company_data['financial_ratios']['combined_ratio']-70))/100,
        company_data['investment_mix']['real_yield']/10
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=val_c, theta=categories, fill='toself', name='החברה הנבחרת', line_color='#00ff00'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), template="plotly_dark", title="פרופיל סיכון-ביצוע")
    return fig

def get_compliance_check(d):
    """בדיקת ציות רגולטורית"""
    return {
        "יחס הון מזערי (>100%)": d['solvency']['solvency_ratio'] >= 100,
        "יחס נזילות (>1.0)": d['financial_ratios']['lcr'] > 1.0,
        "רווחיות חיתומית (CR < 100%)": d['financial_ratios']['combined_ratio'] < 100,
        "איכות הון (Tier 1 > 50%)": d['solvency']['tier1_capital'] / (d['solvency']['tier1_capital'] + d['solvency']['tier2_capital']) > 0.5
    }

# ==============================================================================
# 5. ממשק משתמש (User Interface)
# ==============================================================================

# -- Sidebar --
st.sidebar.title("🛡️ Apex Regulator")
api_key = st.secrets.get("GOOGLE_API_KEY")

st.sidebar.header("⚙️ הגדרות ניתוח")
# הוספת סליידר זמן (חדש)
selected_quarter = st.sidebar.select_slider("רבעון מדווח", options=["Q1 2025", "Q2 2025", "Q3 2025"], value="Q3 2025")
company = st.sidebar.selectbox("חברה מדווחת", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"])
use_sim = st.sidebar.checkbox("🧪 מצב סימולציה (Real Data)", value=True, help="טוען נתוני אמת שהוזנו מראש מדוחות 2025")

st.sidebar.divider()
st.sidebar.header("⚖️ בנצ'מארק")
compare_list = st.sidebar.multiselect("בחר מתחרים להשוואה:", ["Harel", "Phoenix", "Migdal", "Clal", "Menora"], default=["Phoenix", "Migdal"])

st.sidebar.markdown("---")
# כפתור ייצוא (חדש)
if st.sidebar.button("📤 הורד דוח לאקסל"):
    xls_data = generate_excel(company, selected_quarter)
    st.sidebar.download_button(label="שמור קובץ", data=xls_data, file_name=f"{company}_{selected_quarter}_Report.xlsx", mime="application/vnd.ms-excel")

st.sidebar.divider()
st.sidebar.info("v3.0.0 Regulator Edition\nPowered by Gemini & Streamlit")

# -- Main Content --
st.title(f"דשבורד פיקוח רגולטורי: {company} ({selected_quarter})")

if "data" not in st.session_state: st.session_state.data = None

# כפתור הרצה ראשי
if st.button("🚀 הרץ ביקורת (Audit Run)", type="primary"):
    if use_sim:
        with st.spinner(f"טוען פרופיל נתונים מלא עבור {company} ({selected_quarter})..."):
            time.sleep(0.5) 
            # שליפה מהמאגר החדש המלא לפי הרבעון הנבחר
            raw_data = FULL_DATA[selected_quarter].get(company, DEFAULT_MOCK)
            raw_data["meta"] = {"confidence": 0.99, "extraction_time": datetime.utcnow().isoformat() + " (REAL-WORLD)"}
            st.session_state.data = raw_data
    elif api_key:
        path = f"data/{company}/2025/Q1/financial/financial_report.pdf"
        res, status = analyze_report(path, api_key)
        if status == "success": st.session_state.data = res
        else: st.error(status)
    else: st.error("חסר API Key והסימולציה כבויה.")

data = st.session_state.data

# -- Dashboard Display --
if data:
    
    # אזור הערת אקטואר (חדש)
    if "notes" in data:
        st.markdown(f'<div class="actuary-note"><b>📝 הערת אקטואר:</b> {data["notes"]}</div>', unsafe_allow_html=True)

    # 1. דגלים אדומים (Alerts)
    flags = get_red_flags(data)
    if flags:
        st.subheader("🚩 התרעות פיקוח (Regulatory Alerts)")
        for level, msg in flags:
            cls = "alert-critical" if level == "CRITICAL" else "alert-warning"
            st.markdown(f'<div class="alert-box {cls}">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box" style="background-color: #083d08; border-color: #5cb85c; color: #dff0d8;">✅ לא זוהו חריגות רגולטוריות מהותיות.</div>', unsafe_allow_html=True)

    # 2. KPIs (Top Level Metrics)
    k = data['core_kpis']
    cols = st.columns(5)
    metrics_config = [
        ("רווח כולל", "net_profit", "M₪"), 
        ("יתרת CSM", "total_csm", "M₪"), 
        ("סולבנסי", "solvency_ratio", "%", "solvency"), 
        ("GWP (פרמיות)", "gross_premiums", "M₪"), 
        ("ROE", "roe", "%")
    ]
    
    for i, item in enumerate(metrics_config):
        # תמיכה בשליפה מקטגוריות שונות
        if len(item) == 4:
             val = data[item[3]][item[1]]
        else:
             val = k.get(item[1])
             
        cols[i].metric(item[0], fmt(val, item[2]), help=DEFINITIONS.get(item[1], "מדד ביצוע מרכזי"))

    st.divider()

    # 3. Tabs Navigation (מורחב)
    tabs = st.tabs(["📊 IFRS 17", "🛡️ סולבנסי", "💰 השקעות", "📉 יחסים פיננסיים", "⚖️ השוואה", "✅ ציות", "🕹️ סימולטור"])

    # --- TAB 1: IFRS 17 & Models ---
    with tabs[0]:
        s = data['ifrs17_segments']
        st.subheader("ניתוח רווחיות ומודלים (IFRS 17)")
        
        c1, c2 = st.columns([2, 1])
        with c1:
            # הוספת גרף המפל החדש
            st.plotly_chart(create_waterfall(data), use_container_width=True)
        
        with c2:
            # גרף דונאט למודלים
            models = s.get('models', {"PAA": 50, "GMM": 50})
            fig2 = px.pie(values=models.values(), names=models.keys(), hole=0.5, title="מודלי מדידה", color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig2, use_container_width=True)
            st.metric("CSM עסקים חדשים", fmt(s.get('new_business_csm'), "M₪"))

    # --- TAB 2: Solvency ---
    with tabs[1]:
        st.subheader("איתנות פיננסית ואיכות הון")
        sol = data['solvency']
        
        c1, c2 = st.columns([1, 2])
        with c1:
            # הוספת גרף הרדאר החדש
            st.plotly_chart(create_radar_chart(data), use_container_width=True)
            
        with c2:
            # גרף איכות הון (Tier 1 vs Tier 2)
            df_cap = pd.DataFrame({
                "סוג הון": ["Tier 1 (ליבה)", "Tier 2 (משני)"], 
                "סכום": [sol.get('tier1_capital',0), sol.get('tier2_capital',0)]
            })
            fig_cap = px.bar(df_cap, x="סוג הון", y="סכום", color="סוג הון", title="הרכב ההון המוכר", text="סכום")
            fig_cap.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_cap, use_container_width=True)
            
            # טבלת רגישות (חדש)
            st.markdown("#### ניתוח רגישות (Sensitivity)")
            sens_data = {"תרחיש": ["ריבית +1%", "מניות -10%"], "השפעה על יחס": ["+4%", "-2%"], "השפעה על הון": ["+450M", "-200M"]}
            st.dataframe(pd.DataFrame(sens_data), use_container_width=True)

    # --- TAB 3: Investments ---
    with tabs[2]:
        st.subheader("תיק ההשקעות (Nostro)")
        i = data['investment_mix']
        
        c1, c2 = st.columns([2, 1])
        with c1:
            vals = [i.get('govt_bonds_pct',0), i.get('corp_bonds_pct',0), i.get('stocks_pct',0), i.get('real_estate_pct',0), i.get('unquoted_pct',0)]
            names = ["אגח ממשלתי", "אגח קונצרני", "מניות", "נדל\"ן", "לא סחיר (אשראי/קרנות)"]
            fig_inv = px.pie(values=vals, names=names, hole=0.4, title="הקצאת נכסים (Asset Allocation)")
            st.plotly_chart(fig_inv, use_container_width=True)
        
        with c2:
            st.markdown("#### מדדי ביצוע השקעות")
            st.metric("תשואה ריאלית", fmt(i.get('real_yield'), "%"), help=DEFINITIONS["real_yield"])
            st.metric("ROI (תשואה כוללת)", fmt(data['financial_ratios'].get('roi'), "%"), help="תשואה כוללת על התיק")
            st.metric("חשיפה ללא סחיר", fmt(i.get('unquoted_pct'), "%"), help=DEFINITIONS["unquoted_pct"], delta="-גבוה" if i.get('unquoted_pct') > 20 else "תקין", delta_color="inverse")

    # --- TAB 4: Financial Ratios (Added DuPont Logic) ---
    with tabs[3]:
        st.subheader("ניתוח דופונט (DuPont Analysis)")
        r = data['financial_ratios']
        c1, c2, c3 = st.columns(3)
        
        profit = data['core_kpis']['net_profit']
        gwp = data['core_kpis']['gross_premiums']
        assets = data['core_kpis']['total_assets']
        # חישוב דופונט פשוט
        net_margin = (profit / gwp * 100) if gwp else 0
        asset_turn = gwp / assets if assets else 0
        leverage = r.get('leverage', 0)
        
        c1.metric("מרווח רווח (Margin)", fmt(net_margin, "%"), help="רווח נקי חלקי פרמיות")
        c2.metric("מחזור נכסים (Turnover)", fmt(asset_turn, "x"), help="פרמיות חלקי נכסים")
        c3.metric("מינוף (Leverage)", fmt(leverage, "%"))
        st.info(f"ROE מחושב: {fmt(data['core_kpis']['roe'], '%')}")

    # --- TAB 5: Benchmark ---
    with tabs[4]:
        st.subheader("מפת סיכונים ענפית")
        full_compare_list = list(set([company] + compare_list))
        # עדכון פונקציית הבנצ'מארק לקבלת רבעון
        df_bench = get_benchmark_data(full_compare_list, selected_quarter)
        
        if not df_bench.empty:
            
            fig_bench = px.scatter(
                df_bench, 
                x="Solvency", 
                y="ROE", 
                size="CSM", 
                color="Combined", 
                text="חברה", 
                title=f"מפת סיכון-תשואה ({selected_quarter}): Solvency (X) vs ROE (Y)",
                labels={"Solvency": "יחס סולבנסי (%)", "ROE": "תשואה להון (%)", "Combined": "Combined Ratio"},
                color_continuous_scale="RdYlGn_r", # ירוק לנמוך (טוב), אדום לגבוה (רע) עבור Combined Ratio
                size_max=60
            )
            st.plotly_chart(fig_bench, use_container_width=True)
        else:
            st.warning("לא נבחרו חברות להשוואה.")

    # --- TAB 6: Compliance (חדש) ---
    with tabs[5]:
        st.subheader("בקרת ציות (Regulatory Checklist)")
        checks = get_compliance_check(data)
        cc1, cc2 = st.columns(2)
        for i, (k, v) in enumerate(checks.items()):
            col = cc1 if i < 2 else cc2
            icon = "✅" if v else "❌"
            col.markdown(f"#### {icon} {k}")
            if not v: col.error("נדרשת פעולה מתקנת")

    # --- TAB 7: Simulator ---
    with tabs[6]:
        st.subheader("🕹️ סימולטור מבחני קיצון (Stress Test)")
        
        c1, c2 = st.columns(2)
        with c1:
            rate_shock = st.slider("שינוי בריבית חסרת סיכון", -2.0, 2.0, 0.0, 0.1, format="%f%%")
            market_shock = st.slider("נפילה בשוק המניות", -40, 0, 0, 1, format="%f%%")
        with c2:
            lapse_shock = st.slider("גידול בביטולים (Lapse)", 0, 50, 0, 5, format="%f%%")
            quake = st.checkbox("תרחיש קטסטרופה (רעידת אדמה)")
        
        # לוגיקת השפעה (Impact Logic)
        sol_impact = (rate_shock * 12) + (market_shock * 0.45) 
        csm_impact = (rate_shock * 250) + (market_shock * 60) - (lapse_shock * 120)
        if quake: 
            sol_impact -= 15
            csm_impact -= 1500
        
        # חישוב התוצאה החזויה
        base_sol = data['solvency']['solvency_ratio']
        base_csm = data['core_kpis']['total_csm']
        
        pred_sol = base_sol + sol_impact
        pred_csm = base_csm + csm_impact
        
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Solvency חזוי", fmt(pred_sol, "%"), delta=fmt(sol_impact, "%"), delta_color="normal")
        m2.metric("CSM חזוי", fmt(pred_csm, "M₪"), delta=fmt(csm_impact, "M₪"), delta_color="normal")
        
        if pred_sol < 100:
            st.error(f"🚨 התרחיש מוביל לכשל פירעון! (יחס צפוי: {pred_sol:.1f}%)")
        elif pred_sol < 110:
            st.warning(f"⚠️ התרחיש מוביל לאזור מסוכן. (יחס צפוי: {pred_sol:.1f}%)")

# -- Footer --
if not data:
    st.info("אנא בחר חברה ולחץ על כפתור 'הרץ ביקורת' בתפריט הצד.")
