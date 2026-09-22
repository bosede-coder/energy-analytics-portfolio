ERCOT ISO Market Intelligence Dashboard

Portfolio Project 1 of 3 — Energy Analytics
Built by Bose Abubakre, PhD MBA | github.com/boseabubakre

What this is

A real-time market intelligence dashboard for the ERCOT (Electric Reliability Council of Texas) power market; the grid that serves 90% of Texas's electricity load. The dashboard provides operators, traders, analysts, and energy professionals with live visibility into:

- Locational Marginal Prices (LMP)** across ERCOT settlement points
- System load** — actual vs day-ahead forecast
- Generation mix** — by fuel type including wind, solar, natural gas, and nuclear
- Texas weather** — temperature and wind across major load centres (real data via Open-Meteo)
- 90-day price history** — daily min, avg, and max with trend analysis
- Arbitrage opportunity table** — 24-hour price spreads by node

Data sources

| Source | Data | Cost |
|--------|------|------|
| [ERCOT Public API](https://api.ercot.com) | LMP prices, load forecasts, generation mix | Free, no key required |
| [Open-Meteo](https://open-meteo.com) | Weather for Texas load centres | Free, no key required |
| [EIA API](https://api.eia.gov) | National electricity context | Free with API key |

The current version runs on synthetic data that mirrors real ERCOT market patterns. To connect live data, replace the `fetch_*_demo()` functions with the ERCOT API calls documented in the code comments.


Why ERCOT

ERCOT is the most interesting power market in North America for a data scientist:

- It is deregulated, so prices respond directly to supply and demand signals
- It has the largest wind capacity of any US grid and is adding solar rapidly
- It experiences extreme price events — from negative prices during high wind to $9,000/MWh spikes during grid stress
- It is geographically constrained, creating congestion-driven price divergence between nodes
- It serves Houston — the energy capital of the world


Installation and running

bash
Clone the repo
git clone https://github.com/boseabubakre/energy-analytics-portfolio
cd energy-analytics-portfolio/project-1-ercot-dashboard

Install dependencies
pip install -r requirements.txt

Run the dashboard
streamlit run ercot_dashboard.py

The dashboard opens at `http://localhost:8501`

Deploy for free (public URL)

Option 1 — Streamlit Community Cloud (recommended)
1. Push this folder to a public GitHub repo
2. Go to share.streamlit.io and connect your GitHub
3. Deploy — you get a public URL at `yourname-ercot-dashboard.streamlit.app`

Option 2 — Hugging Face Spaces
1. Create a Space at huggingface.co/spaces
2. Choose Streamlit as the SDK
3. Upload the files — instant public deployment


Connecting live ERCOT data

Register for free ERCOT API access at api.ercot.com, then replace the demo functions:

python

Replace fetch_ercot_lmp_demo() with:
def fetch_ercot_lmp_live(node, hours=168):
    endpoint = "https://api.ercot.com/api/public-reports/NP6-905-CD/lmp_by_settlement_point"
    params = {
        "SCEDTimestamp": (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S"),
        "settlementPoint": node,
        "_limit": hours
    }
    r = requests.get(endpoint, params=params, timeout=10)
    return pd.DataFrame(r.json()["data"])

Projects in this portfolio

| Project | Description | Status |
|---------|-------------|--------|
| 1. ERCOT Market Dashboard | Real-time ISO market intelligence | Complete |
| 2. LMP Forecasting Model | Day-ahead price prediction using ML | In progress |
| 3. Battery Optimisation | Energy arbitrage via linear programming and RL | In progress |

About the author

Bose Abubakre, PhD MBA is an AI-powered geoscientist and energy analytics professional based in Dallas, Texas.

- PhD in Paleomagnetism, Rock Magnetism, and Sequence Stratigraphy — University of Johannesburg
- MBA in Strategy and Analytics — Southern Methodist University
- 8 peer-reviewed publications in Journal of Geophysical Research and Gondwana Research
- 10+ years in energy, geoscience, and AI analytics across Nigeria, South Africa, Brazil, and the United States

[LinkedIn](https://linkedin.com/in/boseabubakre) | [GitHub](https://github.com/boseabubakre) | bosedeabuba@gmail.com
