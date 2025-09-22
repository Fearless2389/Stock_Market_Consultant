
# Stock Consultant Agent - Streamlit Deployable

This package provides a Streamlit app (`app.py`) that implements a simple Stock Consultant Agent using mock market data (`mock_market_data.csv`).

## Files
- app.py               -> Streamlit application
- mock_market_data.csv -> Mock market data (ticker,price)
- requirements.txt     -> Python dependencies
- usage.json           -> Persistent usage counters (created/updated by the app)

## Run locally
1. Create a Python virtual environment and activate it.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the app:
   ```
   streamlit run app.py
   ```
4. Open the URL shown by Streamlit (usually http://localhost:8501).

## Deploy to Streamlit Cloud
1. Create a new public GitHub repo and push these files.
2. In Streamlit Cloud, create a new app and point it at the repo and branch.
3. Streamlit Cloud will install `requirements.txt` and run `app.py`.

## CSV formats
- Market CSV: `ticker,price`
- Portfolio CSV (for upload): `ticker,qty,avgPrice(optional)` per row

