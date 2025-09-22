
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Stock Consultant Agent (Streamlit)", layout="wide")

# --- Helpers ---
SECTOR_MAP = {
    "TCS": "IT",
    "INFY": "IT",
    "WIPRO": "IT",
    "HDFCBANK": "Financials",
    "ICICIBANK": "Financials",
    "RELIANCE": "Energy",
    "LT": "Industrials",
    "AXISBANK": "Financials",
    "HINDUNILVR": "Consumer",
    "SBIN": "Financials",
}

def human_advice(percent_change, holding_pct):
    if percent_change is None:
        return "NO DATA — latest price unavailable."
    if percent_change <= -15:
        return "STRONG BUY — price dropped a lot; consider adding if you believe in the company."
    if percent_change <= -5:
        return "BUY — price is down; looks attractive for accumulation."
    if percent_change <= 5:
        return "HOLD — no strong signal; monitor."
    if percent_change <= 15:
        return "HOLD / REDUCE — price rose; consider taking partial profits."
    if holding_pct > 0.25:
        return "SELL — position is large and price increased significantly; trim to reduce risk."
    return "REDUCE — price up a lot; lock in gains or rebalance."

# usage persistence
USAGE_FILE = "usage.json"
if not os.path.exists(USAGE_FILE):
    with open(USAGE_FILE, "w") as f:
        json.dump({"portfolios_analyzed": 0, "advices_generated": 0, "events": []}, f)

def read_usage():
    with open(USAGE_FILE, "r") as f:
        return json.load(f)

def write_usage(u):
    with open(USAGE_FILE, "w") as f:
        json.dump(u, f, indent=2)

# --- Load market mock data (CSV) ---
MARKET_CSV = "mock_market_data.csv"
@st.cache_data
def load_market():
    if os.path.exists(MARKET_CSV):
        df = pd.read_csv(MARKET_CSV)
        df['ticker'] = df['ticker'].astype(str).str.upper()
        return df.set_index('ticker')
    else:
        return pd.DataFrame(columns=['price'])

market_df = load_market()

# --- UI ---
st.title("Stock Consultant Agent — Streamlit Demo")
st.markdown("Simple advisor: enter your portfolio, click **Analyze**, and get plain-English advice (BUY / SELL / HOLD / DIVERSIFY).")

with st.sidebar:
    st.header("Config & Billing")
    price_per_advice = st.number_input("Price per advice (USD)", min_value=0.0, value=0.02, step=0.01, format="%.4f")
    price_per_portfolio = st.number_input("Price per portfolio (USD)", min_value=0.0, value=0.10, step=0.01, format="%.4f")
    st.markdown("---")
    st.header("Upload")
    uploaded_market = st.file_uploader("Replace mock market CSV (ticker,price)", type=["csv"])
    if uploaded_market is not None:
        try:
            mf = pd.read_csv(uploaded_market)
            mf.to_csv(MARKET_CSV, index=False)
            st.success("Market CSV uploaded and saved.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to save market CSV: {e}")

st.subheader("Market snapshot (mock data)")
st.dataframe(market_df.reset_index().rename(columns={"index": "ticker"}))

# Portfolio input
st.subheader("Enter portfolio")
col1, col2, col3, col4 = st.columns([2,1,1,1])
with col1:
    t_in = st.text_input("Ticker (e.g., TCS)", key="t_in")
with col2:
    q_in = st.number_input("Qty", min_value=0.0, value=0.0, step=1.0, key="q_in")
with col3:
    a_in = st.number_input("Avg price (optional)", min_value=0.0, value=0.0, step=0.01, key="a_in")
with col4:
    add_btn = st.button("Add to portfolio")

if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = []

if add_btn:
    if t_in:
        st.session_state.portfolio.append({"ticker": t_in.upper().strip(), "qty": float(q_in), "avgPrice": float(a_in) if a_in>0 else None})
        st.experimental_rerun()
    else:
        st.warning("Enter a ticker before adding.")

st.markdown("Or upload a CSV with rows: `ticker,qty,avgPrice(optional)`")
uploaded_port = st.file_uploader("Upload portfolio CSV", type=["csv"], key="pf")

if uploaded_port is not None:
    try:
        pdf = pd.read_csv(uploaded_port, header=None)
        for _, row in pdf.iterrows():
            ticker = str(row[0]).upper().strip()
            qty = float(row[1])
            avg = float(row[2]) if len(row) > 2 and not pd.isna(row[2]) else None
            st.session_state.portfolio.append({"ticker": ticker, "qty": qty, "avgPrice": avg})
        st.success("Portfolio uploaded.")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Failed to read portfolio CSV: {e}")

# Show current portfolio
st.write("### Current positions")
if len(st.session_state.portfolio) == 0:
    st.info("No positions yet. Add rows or upload CSV.")
else:
    pf_df = pd.DataFrame(st.session_state.portfolio)
    st.dataframe(pf_df)

# Analyze
if st.button("Analyze portfolio"):

    if len(st.session_state.portfolio) == 0:
        st.warning("Portfolio is empty.")
    else:
        # compute total value
        total_value = 0.0
        enriched = []
        for r in st.session_state.portfolio:
            ticker = r['ticker'].upper()
            qty = float(r['qty'])
            latest = None
            if ticker in market_df.index:
                latest = float(market_df.loc[ticker, 'price'])
            avg = r['avgPrice'] if r['avgPrice'] is not None and r['avgPrice']>0 else latest
            value = (latest if latest is not None else avg if avg is not None else 0.0) * qty
            total_value += value
            enriched.append({"ticker": ticker, "qty": qty, "avg": avg, "latest": latest, "value": value})
        # calculate sector counts
        sector_values = {}
        for e in enriched:
            sec = SECTOR_MAP.get(e['ticker'], 'Unknown')
            sector_values[sec] = sector_values.get(sec, 0.0) + e['value']
        # build analysis rows
        analysis = []
        for e in enriched:
            latest = e['latest']
            avg = e['avg'] if e['avg'] is not None else (latest if latest is not None else 0.0)
            percent_change = None
            if latest is not None and avg != 0:
                percent_change = ((latest - avg) / avg) * 100.0
            holding_pct = (e['value'] / total_value) if total_value > 0 else 0.0
            advice = human_advice(percent_change, holding_pct)
            analysis.append({**e, "percent_change": percent_change, "holding_pct": holding_pct, "advice": advice, "sector": SECTOR_MAP.get(e['ticker'], 'Unknown')})

        # Display analysis
        st.success("Analysis complete — plain-English advice below.")
        for row in analysis:
            st.markdown(f"**{row['ticker']}** ({row['sector']}) — Latest: {row['latest'] if row['latest'] is not None else 'N/A'} — Value: {row['value']:.2f} — Holding %: {row['holding_pct']*100:.2f}%")
            st.write(f"Advice: {row['advice']}")
            st.write("---")

        # Update usage counters
        u = read_usage()
        u['portfolios_analyzed'] += 1
        u['advices_generated'] += len(analysis)
        u['events'].append({"ts": datetime.utcnow().isoformat(), "advices": len(analysis), "portfolio_size": len(analysis)})
        write_usage(u)

        st.info(f"Portfolios analyzed (total): {u['portfolios_analyzed']} — Advices generated (total): {u['advices_generated']}")
        est_bill = price_per_portfolio * u['portfolios_analyzed'] + price_per_advice * u['advices_generated']
        st.info(f"Estimated bill so far: ${est_bill:.4f}")

# Controls
st.markdown("---")
if st.button("Reset portfolio (session only)"):
    st.session_state.portfolio = []
    st.experimental_rerun()

if st.button("Reset usage counters (persistent)"):
    write_usage({"portfolios_analyzed": 0, "advices_generated": 0, "events": []})
    st.experimental_rerun()
