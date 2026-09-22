"""
ERCOT ISO Market Intelligence Dashboard
Author: Bose Abubakre, PhD MBA
Portfolio: Energy Analytics | AI-Powered Geoscientist

Data Sources:
- ERCOT Public API (api.ercot.com) - LMP prices, load forecasts, generation mix
- Open-Meteo API (open-meteo.com) - Weather data, free, no key required
- EIA API (api.eia.gov) - National context, free with key

Run: streamlit run ercot_dashboard.py
Install: pip install streamlit pandas plotly requests numpy
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ERCOT Market Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS: Control Room Dark Theme ───────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0047AB;
    color: #e0edff;
  }
  .main { background-color: #0047AB; }
  .stApp { background-color: #0047AB; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #3a7bd5;
    border-radius: 6px;
    padding: 12px 16px;
  }
  [data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #e8f0ff;
    letter-spacing: 0.08em;
  }
  [data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 26px;
    color: #f0a500;
    font-weight: 500;
  }
  [data-testid="stMetricDelta"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #0057C8;
    border-right: 1px solid #3a7bd5;
  }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stDateInput label {
    color: #e8f0ff;
    font-size: 12px;
    font-family: 'IBM Plex Mono', monospace;
  }

  /* Headers */
  h1 { color: #ffffff; font-weight: 600; font-size: 20px !important; }
  h2 { color: #ffffff; font-weight: 500; font-size: 15px !important; border-bottom: 1px solid #3a7bd5; padding-bottom: 6px; }
  h3 { color: #e8f0ff; font-weight: 400; font-size: 13px !important; }

  /* Status badge */
  .status-live {
    display: inline-block;
    background: #1a5fb4;
    color: #3fb950;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    border: 1px solid #3fb950;
    margin-left: 8px;
  }
  .status-demo {
    display: inline-block;
    background: #1a5fb4;
    color: #f0a500;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    border: 1px solid #f0a500;
    margin-left: 8px;
  }

  /* Section divider */
  hr { border: none; border-top: 1px solid #3a7bd5; margin: 8px 0; }

  /* Info box */
  .info-box {
    background: #161b22;
    border: 1px solid #3a7bd5;
    border-left: 3px solid #58a6ff;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 13px;
    color: #e8f0ff;
    margin: 8px 0;
  }

  /* Plotly chart background */
  .js-plotly-plot { border-radius: 6px; }

  /* Hide streamlit branding */
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── CHART TEMPLATE ────────────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor="#0057C8",
    plot_bgcolor="#0047AB",
    font=dict(family="IBM Plex Mono", color="#e8f0ff", size=11),
    xaxis=dict(gridcolor="#3a7bd5", linecolor="#3a7bd5", zerolinecolor="#3a7bd5"),
    yaxis=dict(gridcolor="#3a7bd5", linecolor="#3a7bd5", zerolinecolor="#3a7bd5"),
    margin=dict(l=50, r=20, t=40, b=40),
    legend=dict(bgcolor="#0057C8", bordercolor="#3a7bd5", borderwidth=1)
)

def chart_layout(**overrides):
    """Return chart layout with optional overrides."""
    base = CHART_LAYOUT.copy()
    base.update(overrides)
    return base
AMBER  = "#f0a500"
BLUE   = "#58a6ff"
GREEN  = "#3fb950"
RED    = "#f85149"
PURPLE = "#bc8cff"
TEAL   = "#39d353"

# ── DATA FETCHING ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_ercot_lmp_demo():
    """
    Generates realistic ERCOT LMP data.
    In production: replace with ERCOT Public API
    Register at: https://api.ercot.com
    Endpoint: /api/public-reports/NP6-905-CD/lmp_by_settlement_point
    """
    np.random.seed(42)
    now = datetime.now()
    hours = pd.date_range(end=now, periods=168, freq="h")  # 7 days

    # Realistic ERCOT price patterns
    hour_of_day = hours.hour
    day_of_week = hours.dayofweek

    # Base price with time-of-day pattern
    base = 35 + 20 * np.sin((hour_of_day - 6) * np.pi / 12)
    # Weekend discount
    weekend = np.where(day_of_week >= 5, -8, 0)
    # Morning and evening peaks
    peak = (
        15 * np.exp(-0.5 * ((hour_of_day - 8) / 2) ** 2) +
        18 * np.exp(-0.5 * ((hour_of_day - 18) / 1.5) ** 2)
    )
    # Random noise and occasional price spikes
    noise = np.random.normal(0, 5, len(hours))
    spikes = np.where(np.random.random(len(hours)) > 0.97, np.random.uniform(80, 250, len(hours)), 0)
    lmp = base + weekend + peak + noise + spikes
    lmp = np.maximum(lmp, -5)  # ERCOT can go negative

    nodes = {
        "HB_HOUSTON":  lmp + np.random.normal(0, 3, len(hours)),
        "HB_NORTH":    lmp + np.random.normal(-2, 3, len(hours)),
        "HB_WEST":     lmp + np.random.normal(-8, 6, len(hours)),  # Wind-heavy, lower prices
        "HB_SOUTH":    lmp + np.random.normal(1, 4, len(hours)),
        "LZ_HOUSTON":  lmp + np.random.normal(2, 2, len(hours)),
    }
    df = pd.DataFrame(nodes, index=hours)
    df.index.name = "timestamp"
    return df

@st.cache_data(ttl=300)
def fetch_load_forecast_demo():
    """
    Realistic ERCOT load forecast.
    In production: /api/public-reports/NP3-566-CD/2d_aheadstlmnt_pnt_load_fcst
    """
    np.random.seed(123)
    now = datetime.now()
    hours = pd.date_range(start=now, periods=48, freq="h")
    hour_of_day = hours.hour
    base_load = 45000
    daily_pattern = (
        -8000 * np.cos(2 * np.pi * hour_of_day / 24) +
        3000 * np.exp(-0.5 * ((hour_of_day - 15) / 3) ** 2)
    )
    noise = np.random.normal(0, 500, 48)
    forecast_load = base_load + daily_pattern + noise
    actual_load = forecast_load[:24] + np.random.normal(0, 300, 24)
    return pd.DataFrame({
        "timestamp": hours,
        "forecast_mw": forecast_load,
        "actual_mw": np.concatenate([actual_load, [np.nan] * 24])
    }).set_index("timestamp")

@st.cache_data(ttl=300)
def fetch_generation_mix_demo():
    """
    ERCOT generation by fuel type.
    In production: /api/public-reports/NP4-745-CD/spp_hrly_actual_fcast_geo
    """
    fuels = {
        "Natural Gas":  38.2,
        "Wind":         26.4,
        "Solar":        14.1,
        "Nuclear":      10.8,
        "Coal":          7.3,
        "Hydro":         1.8,
        "Other":         1.4,
    }
    colors_map = {
        "Natural Gas": "#f0a500",
        "Wind":        "#58a6ff",
        "Solar":       "#ffa657",
        "Nuclear":     "#bc8cff",
        "Coal":        "#6e7681",
        "Hydro":       "#39d353",
        "Other":       "#8b949e",
    }
    return fuels, colors_map

@st.cache_data(ttl=600)
def fetch_weather_texas():
    """
    Real weather data via Open-Meteo (free, no API key required).
    Covers major ERCOT load centers.
    """
    cities = {
        "Houston":  (29.76, -95.37),
        "Dallas":   (32.78, -96.80),
        "San Antonio": (29.42, -98.49),
        "Austin":   (30.27, -97.74),
    }
    results = {}
    for city, (lat, lon) in cities.items():
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&hourly=temperature_2m,wind_speed_10m,shortwave_radiation"
                f"&temperature_unit=fahrenheit"
                f"&wind_speed_unit=mph"
                f"&forecast_days=2"
                f"&timezone=America%2FChicago"
            )
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                d = r.json()
                df = pd.DataFrame({
                    "timestamp": pd.to_datetime(d["hourly"]["time"]),
                    "temp_f":    d["hourly"]["temperature_2m"],
                    "wind_mph":  d["hourly"]["wind_speed_10m"],
                    "solar_wm2": d["hourly"]["shortwave_radiation"],
                })
                results[city] = df
        except Exception:
            pass
    return results

@st.cache_data(ttl=300)
def fetch_price_history_demo():
    """Extended price history for analysis."""
    np.random.seed(99)
    days = pd.date_range(end=datetime.now(), periods=90, freq="D")
    daily_avg = 38 + 12 * np.sin(2 * np.pi * np.arange(90) / 30) + np.random.normal(0, 6, 90)
    daily_max = daily_avg + np.random.uniform(15, 60, 90)
    daily_min = daily_avg - np.random.uniform(5, 25, 90)
    return pd.DataFrame({
        "date": days,
        "avg_lmp": daily_avg,
        "max_lmp": daily_max,
        "min_lmp": np.maximum(daily_min, -10)
    }).set_index("date")

# ── HEADER ────────────────────────────────────────────────────────────────────
col_title, col_badge, col_time = st.columns([4, 1, 2])
with col_title:
    st.markdown("## ⚡ ERCOT Market Intelligence")
with col_badge:
    st.markdown('<span class="status-demo">DEMO MODE</span>', unsafe_allow_html=True)
with col_time:
    st.markdown(
        f'<div style="text-align:right;font-family:IBM Plex Mono;font-size:12px;color:#8b949e;margin-top:6px">'
        f'{datetime.now().strftime("%Y-%m-%d  %H:%M")} CT</div>',
        unsafe_allow_html=True)

st.markdown('<div class="info-box">📡 Running on synthetic data that mirrors real ERCOT market patterns. '
            'Connect to the <b>ERCOT Public API</b> (api.ercot.com) and '
            '<b>Open-Meteo</b> (open-meteo.com) for live data — both are free.</div>',
            unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Market Controls")
    selected_node = st.selectbox(
        "Settlement Point",
        ["HB_HOUSTON", "HB_NORTH", "HB_WEST", "HB_SOUTH", "LZ_HOUSTON"],
        index=0
    )
    lookback_days = st.slider("History (days)", 1, 7, 3)
    st.markdown("---")
    st.markdown("### Data Sources")
    st.markdown("""
    <div style='font-family:IBM Plex Mono;font-size:11px;color:#8b949e;line-height:1.8'>
    🔌 ERCOT Public API<br>
    &nbsp;&nbsp;api.ercot.com<br>
    &nbsp;&nbsp;Free · No key required<br><br>
    🌤 Open-Meteo Weather<br>
    &nbsp;&nbsp;open-meteo.com<br>
    &nbsp;&nbsp;Free · No key required<br><br>
    ⚡ EIA National Data<br>
    &nbsp;&nbsp;api.eia.gov<br>
    &nbsp;&nbsp;Free with API key
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <div style='font-family:IBM Plex Mono;font-size:10px;color:#6e7681;line-height:1.6'>
    Built by Bose Abubakre<br>
    PhD Geoscientist · MBA<br>
    Energy Analytics Portfolio<br>
    github.com/boseabubakre
    </div>
    """, unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
lmp_df      = fetch_ercot_lmp_demo()
load_df     = fetch_load_forecast_demo()
gen_mix, gen_colors = fetch_generation_mix_demo()
weather     = fetch_weather_texas()
price_hist  = fetch_price_history_demo()

# Current values
current_lmp  = lmp_df[selected_node].iloc[-1]
prev_hour    = lmp_df[selected_node].iloc[-2]
lmp_delta    = current_lmp - prev_hour
current_load = load_df["actual_mw"].dropna().iloc[-1] if load_df["actual_mw"].dropna().shape[0] > 0 else load_df["forecast_mw"].iloc[0]
houston_temp = weather.get("Houston", pd.DataFrame()).get("temp_f", pd.Series([88])).iloc[0] if weather else 88
daily_avg    = lmp_df[selected_node].tail(24).mean()
weekly_avg   = lmp_df[selected_node].mean()

# ── KPI STRIP ────────────────────────────────────────────────────────────────
st.markdown("#### Real-Time Market Snapshot")
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric(f"LMP  {selected_node}", f"${current_lmp:.2f}/MWh",
              delta=f"{lmp_delta:+.2f} vs prev hr")
with k2:
    st.metric("System Load", f"{current_load/1000:.1f} GW",
              delta=f"Peak forecast {load_df['forecast_mw'].max()/1000:.1f} GW")
with k3:
    st.metric("24-hr Avg LMP", f"${daily_avg:.2f}/MWh",
              delta=f"{daily_avg - weekly_avg:+.2f} vs 7-day avg")
with k4:
    st.metric("Houston Temp", f"{houston_temp:.0f}°F",
              delta="Cooling demand driver")
with k5:
    wind_pct = gen_mix["Wind"]
    st.metric("Wind Generation", f"{wind_pct:.1f}%",
              delta="of grid mix now")

st.markdown("---")

# ── ROW 1: LMP + GENERATION MIX ──────────────────────────────────────────────
col_lmp, col_gen = st.columns([3, 2])

with col_lmp:
    st.markdown(f"#### LMP Price History — {selected_node}")
    plot_df = lmp_df.tail(lookback_days * 24)

    fig_lmp = go.Figure()
    # All nodes faint
    for node in lmp_df.columns:
        if node != selected_node:
            fig_lmp.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df[node],
                mode="lines", name=node,
                line=dict(color="#21262d", width=1),
                showlegend=True, opacity=0.5
            ))
    # Selected node prominent
    fig_lmp.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df[selected_node],
        mode="lines", name=selected_node,
        line=dict(color=AMBER, width=2.5),
        fill="tozeroy", fillcolor="rgba(240,165,0,0.10)"
    ))
    # Price spike zones
    spike_mask = plot_df[selected_node] > 100
    if spike_mask.any():
        fig_lmp.add_trace(go.Scatter(
            x=plot_df.index[spike_mask], y=plot_df[selected_node][spike_mask],
            mode="markers", name="Price spike",
            marker=dict(color=RED, size=6, symbol="circle")
        ))
    fig_lmp.update_layout(**chart_layout(height=300, yaxis_title="$/MWh", xaxis_title=None, hovermode="x unified"))
    st.plotly_chart(fig_lmp, use_container_width=True)

with col_gen:
    st.markdown("#### Generation Mix")
    fuels  = list(gen_mix.keys())
    values = list(gen_mix.values())
    colors = [gen_colors[f] for f in fuels]

    fig_gen = go.Figure(go.Pie(
        labels=fuels, values=values,
        marker_colors=colors,
        hole=0.55,
        textinfo="label+percent",
        textfont=dict(family="IBM Plex Mono", size=10, color="#e0edff"),
        hovertemplate="%{label}: %{value:.1f}%<extra></extra>"
    ))
    fig_gen.add_annotation(
        text="Grid<br>Mix", x=0.5, y=0.5,
        font=dict(family="IBM Plex Mono", size=13, color="#e8f0ff"),
        showarrow=False
    )
    fig_gen.update_layout(**chart_layout(height=300, showlegend=False, margin=dict(l=10, r=10, t=30, b=10)))
    st.plotly_chart(fig_gen, use_container_width=True)

# ── ROW 2: LOAD FORECAST + WEATHER ───────────────────────────────────────────
col_load, col_wx = st.columns([3, 2])

with col_load:
    st.markdown("#### 48-Hour Load Forecast vs Actual")
    fig_load = go.Figure()
    fig_load.add_trace(go.Scatter(
        x=load_df.index, y=load_df["forecast_mw"] / 1000,
        mode="lines", name="Forecast",
        line=dict(color=BLUE, width=2, dash="dot")
    ))
    fig_load.add_trace(go.Scatter(
        x=load_df.index, y=load_df["actual_mw"] / 1000,
        mode="lines", name="Actual",
        line=dict(color=GREEN, width=2.5)
    ))
    fig_load.add_vline(
        x=datetime.now().timestamp() * 1000,
        line=dict(color="#e8f0ff", dash="dash", width=1),
        annotation_text="now",
        annotation_font=dict(color="#e8f0ff", size=10, family="IBM Plex Mono")
    )
    fig_load.update_layout(**chart_layout(height=260, yaxis_title="GW", hovermode="x unified"))
    st.plotly_chart(fig_load, use_container_width=True)

with col_wx:
    st.markdown("#### Texas Weather — Load Drivers")
    if weather:
        city = st.selectbox("City", list(weather.keys()), label_visibility="collapsed")
        wx_df = weather[city].head(24)
        fig_wx = go.Figure()
        fig_wx.add_trace(go.Scatter(
            x=wx_df["timestamp"], y=wx_df["temp_f"],
            mode="lines+markers", name="Temp (°F)",
            line=dict(color=AMBER, width=2),
            marker=dict(size=4)
        ))
        fig_wx2 = go.Figure()
        fig_wx.add_trace(go.Bar(
            x=wx_df["timestamp"], y=wx_df["wind_mph"],
            name="Wind (mph)", yaxis="y2",
            marker_color=BLUE, opacity=0.4
        ))
        fig_wx.update_layout(**chart_layout(height=260, yaxis=dict(title="°F", gridcolor="#3a7bd5"), yaxis2=dict(title="mph", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)"), legend=dict(orientation="h", y=1.1), hovermode="x unified"))
        st.plotly_chart(fig_wx, use_container_width=True)
    else:
        st.info("Weather API unavailable. Check internet connection.")

# ── ROW 3: PRICE HISTORY + NODE HEATMAP ──────────────────────────────────────
col_hist, col_heat = st.columns([3, 2])

with col_hist:
    st.markdown("#### 90-Day Price History")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=price_hist.index, y=price_hist["max_lmp"],
        mode="lines", name="Daily Max",
        line=dict(color=RED, width=1, dash="dot"), fill=None
    ))
    fig_hist.add_trace(go.Scatter(
        x=price_hist.index, y=price_hist["avg_lmp"],
        mode="lines", name="Daily Avg",
        line=dict(color=AMBER, width=2),
        fill="tonexty", fillcolor="rgba(240,165,0,0.12)"
    ))
    fig_hist.add_trace(go.Scatter(
        x=price_hist.index, y=price_hist["min_lmp"],
        mode="lines", name="Daily Min",
        line=dict(color=BLUE, width=1, dash="dot"),
        fill="tonexty", fillcolor="rgba(88,166,255,0.08)"
    ))
    fig_hist.update_layout(**chart_layout(height=260, yaxis_title="$/MWh", hovermode="x unified"))
    st.plotly_chart(fig_hist, use_container_width=True)

with col_heat:
    st.markdown("#### Node Price Comparison — Now")
    nodes_now = {n: lmp_df[n].iloc[-1] for n in lmp_df.columns}
    nodes_df = pd.DataFrame.from_dict(
        nodes_now, orient="index", columns=["lmp"]
    ).sort_values("lmp", ascending=True)

    fig_bar = go.Figure(go.Bar(
        x=nodes_df["lmp"],
        y=nodes_df.index,
        orientation="h",
        marker_color=[AMBER if n == selected_node else "#21262d" for n in nodes_df.index],
        marker_line_color=[AMBER if n == selected_node else "#30363d" for n in nodes_df.index],
        marker_line_width=1.5,
        text=[f"${v:.2f}" for v in nodes_df["lmp"]],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=10, color="#e8f0ff")
    ))
    fig_bar.update_layout(**chart_layout(height=260, xaxis_title="$/MWh", margin=dict(l=10, r=60, t=20, b=30)))
    st.plotly_chart(fig_bar, use_container_width=True)

# ── ROW 4: ARBITRAGE OPPORTUNITY TABLE ───────────────────────────────────────
st.markdown("---")
st.markdown("#### Arbitrage Opportunity Analysis — 24hr Spread")

spread_data = []
for node in lmp_df.columns:
    series = lmp_df[node].tail(24)
    spread_data.append({
        "Settlement Point": node,
        "Min $/MWh":        f"${series.min():.2f}",
        "Max $/MWh":        f"${series.max():.2f}",
        "Spread $/MWh":     f"${series.max() - series.min():.2f}",
        "Avg $/MWh":        f"${series.mean():.2f}",
        "Std Dev":          f"${series.std():.2f}",
        "Negative hrs":     int((series < 0).sum()),
        "Spike hrs (>100)": int((series > 100).sum()),
    })

spread_df = pd.DataFrame(spread_data)
st.dataframe(
    spread_df,
    use_container_width=True,
    hide_index=True,
    height=220
)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='font-family:IBM Plex Mono;font-size:10px;color:#6e7681;text-align:center;padding:8px'>
ERCOT Market Intelligence Dashboard &nbsp;·&nbsp;
Built by Bose Abubakre, PhD MBA &nbsp;·&nbsp;
github.com/boseabubakre &nbsp;·&nbsp;
Data: ERCOT Public API + Open-Meteo &nbsp;·&nbsp;
For portfolio and research use only — not financial advice
</div>
""", unsafe_allow_html=True)
