import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Vedhi Pulse", layout="wide", page_icon="📈")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,400;1,600&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"], p, span, div {
    font-family: 'Inter', sans-serif !important;
}
.vedhi-brand {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic;
    font-weight: 700;
    font-size: 46px;
    color: #1A1A18;
    letter-spacing: -1.5px;
    line-height: 1.1;
}
.vedhi-brand .pulse {
    color: #1D9E75;
}
.vedhi-sub {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 400;
    color: #999;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 6px;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #EAF3DE;
    color: #27500A;
    font-size: 10px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 8px;
}
.live-dot-c {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #1D9E75;
    display: inline-block;
    animation: blink 1.5s infinite;
}
@keyframes blink {0%,100%{opacity:1}50%{opacity:.2}}
.metric-card{background:#F7F7F5;border-radius:10px;padding:14px 18px;margin-bottom:8px}
.green{color:#1D9E75;font-weight:600}
.red{color:#E24B4A;font-weight:600}
.blue{color:#185FA5;font-weight:600}
.orange{color:#D85A30;font-weight:600}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:8px 0 20px">
  <div class="vedhi-brand">Vedhi <span class="pulse">Pulse</span></div>
  <div class="vedhi-sub">Nifty 50 Intelligence &nbsp;&middot;&nbsp; NSE India &nbsp;&middot;&nbsp; Live Market Data</div>
  <div class="live-badge"><span class="live-dot-c"></span>&nbsp;Live</div>
</div>
""", unsafe_allow_html=True)

# ── Nifty 50 Index Live Indicators ──────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_nifty_indicators():
    try:
        df = yf.download("^NSEI", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 55:
            return None
        close = df["Close"].squeeze()
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
        delta = close.diff()
        gain  = delta.where(delta>0,0).rolling(14).mean()
        loss  = (-delta.where(delta<0,0)).rolling(14).mean()
        rsi   = (100 - (100/(1+gain/loss.replace(0,1e-10)))).iloc[-1]
        ema12     = close.ewm(span=12, adjust=False).mean()
        ema26     = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal    = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal
        ltp  = close.iloc[-1]
        prev = close.iloc[-2]
        chg  = ltp - prev
        chgp = (chg/prev)*100
        return {
            "ltp":float(ltp), "chg":float(chg), "chgp":float(chgp),
            "rsi":round(float(rsi),1),
            "ema20":round(float(ema20),1),
            "ema50":round(float(ema50),1),
            "macd":round(float(macd_line.iloc[-1]),2),
            "signal":round(float(signal.iloc[-1]),2),
            "histogram":round(float(histogram.iloc[-1]),2),
        }
    except Exception as e:
        return None

nifty = fetch_nifty_indicators()

if nifty:
    st.markdown("### Nifty 50 — Live Technical Indicators")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    chg_sign = "+" if nifty["chg"] >= 0 else ""
    arrow    = "▲" if nifty["chg"] >= 0 else "▼"

    col1.metric(
        "Nifty 50",
        f"{nifty['ltp']:,.2f}",
        f"{arrow} {abs(nifty['chg']):.2f} ({abs(nifty['chgp']):.2f}%)"
    )
    rsi_label = "Oversold" if nifty["rsi"]<30 else "Value zone" if nifty["rsi"]<40 else "Neutral" if nifty["rsi"]<60 else "Elevated" if nifty["rsi"]<70 else "Overbought"
    col2.metric("RSI (14)", f"{nifty['rsi']}", rsi_label)
    col3.metric("EMA 20", f"{nifty['ema20']:,.1f}",
                "Price above" if nifty["ltp"] > nifty["ema20"] else "Price below")
    col4.metric("EMA 50", f"{nifty['ema50']:,.1f}",
                "Price above" if nifty["ltp"] > nifty["ema50"] else "Price below")
    col5.metric("MACD", f"{nifty['macd']:+.2f}",
                f"Signal {nifty['signal']:+.2f}")
    col6.metric("Histogram", f"{nifty['histogram']:+.2f}",
                "Bullish" if nifty["histogram"] >= 0 else "Bearish")

    st.caption(f"Auto-refreshes every 5 min | Source: Yahoo Finance | {pd.Timestamp.now().strftime('%d %b %Y %H:%M')} IST")
else:
    st.warning("Could not fetch Nifty 50 data — please refresh the page.")

st.divider()

# ── Nifty 50 tickers ─────────────────────────────────────────────────────────
NIFTY50 = {
    "ADANIENT":   {"sector":"Conglomerate", "lot":309},
    "ADANIPORTS": {"sector":"Ports",        "lot":475},
    "APOLLOHOSP": {"sector":"Healthcare",   "lot":125},
    "ASIANPAINT": {"sector":"Paint",        "lot":250},
    "AXISBANK":   {"sector":"Bank",         "lot":625},
    "BAJAJ-AUTO": {"sector":"Auto",         "lot":75},
    "BAJFINANCE": {"sector":"NBFC",         "lot":750},
    "BAJAJFINSV": {"sector":"NBFC",         "lot":250},
    "BEL":        {"sector":"Defence",      "lot":1425},
    "BPCL":       {"sector":"Energy",       "lot":1975},
    "BHARTIARTL": {"sector":"Telecom",      "lot":475},
    "BRITANNIA":  {"sector":"FMCG",         "lot":125},
    "CIPLA":      {"sector":"Pharma",       "lot":375},
    "COALINDIA":  {"sector":"Energy",       "lot":1350},
    "DIVISLAB":   {"sector":"Pharma",       "lot":100},
    "DRREDDY":    {"sector":"Pharma",       "lot":625},
    "EICHERMOT":  {"sector":"Auto",         "lot":100},
    "GRASIM":     {"sector":"Cement",       "lot":250},
    "HCLTECH":    {"sector":"IT",           "lot":350},
    "HDFCBANK":   {"sector":"Bank",         "lot":550},
    "HDFCLIFE":   {"sector":"Insurance",    "lot":1100},
    "HEROMOTOCO": {"sector":"Auto",         "lot":150},
    "HINDALCO":   {"sector":"Metal",        "lot":700},
    "HINDUNILVR": {"sector":"FMCG",         "lot":300},
    "ICICIBANK":  {"sector":"Bank",         "lot":700},
    "ITC":        {"sector":"FMCG",         "lot":1600},
    "INDUSINDBK": {"sector":"Bank",         "lot":700},
    "INFY":       {"sector":"IT",           "lot":400},
    "JSWSTEEL":   {"sector":"Metal",        "lot":675},
    "KOTAKBANK":  {"sector":"Bank",         "lot":2000},
    "LT":         {"sector":"Infra",        "lot":175},
    "M&M":        {"sector":"Auto",         "lot":200},
    "MARUTI":     {"sector":"Auto",         "lot":50},
    "NTPC":       {"sector":"PSU Power",    "lot":1500},
    "NESTLEIND":  {"sector":"FMCG",         "lot":500},
    "ONGC":       {"sector":"Energy",       "lot":2250},
    "POWERGRID":  {"sector":"PSU Power",    "lot":1900},
    "RELIANCE":   {"sector":"Conglomerate", "lot":500},
    "SBILIFE":    {"sector":"Insurance",    "lot":375},
    "SHRIRAMFIN": {"sector":"NBFC",         "lot":825},
    "SBIN":       {"sector":"PSU Bank",     "lot":750},
    "SUNPHARMA":  {"sector":"Pharma",       "lot":350},
    "TCS":        {"sector":"IT",           "lot":175},
    "TATACONSUM": {"sector":"FMCG",         "lot":550},
    "TATAMOTORS": {"sector":"Auto",         "lot":1425},
    "TATASTEEL":  {"sector":"Metal",        "lot":2750},
    "TECHM":      {"sector":"IT",           "lot":600},
    "TITAN":      {"sector":"Consumer",     "lot":175},
    "ULTRACEMCO": {"sector":"Cement",       "lot":50},
    "WIPRO":      {"sector":"IT",           "lot":3000},
}

# ── Indicator functions ───────────────────────────────────────────────────────
def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast   = series.ewm(span=fast, adjust=False).mean()
    ema_slow   = series.ewm(span=slow, adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line= macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram

# ── Fetch one stock ───────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_stock(symbol):
    try:
        df = yf.download(f"{symbol}.NS", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 55:
            return None
        close = df["Close"].squeeze()
        ema20 = calc_ema(close, 20).iloc[-1]
        ema50 = calc_ema(close, 50).iloc[-1]
        rsi   = calc_rsi(close).iloc[-1]
        macd_line, signal_line, histogram = calc_macd(close)
        ltp   = close.iloc[-1]
        prev  = close.iloc[-2]
        chg   = ltp - prev
        chg_pct = (chg / prev) * 100
        return {
            "LTP":       round(float(ltp), 2),
            "Change":    round(float(chg), 2),
            "Chg%":      round(float(chg_pct), 2),
            "RSI":       round(float(rsi), 1),
            "EMA20":     round(float(ema20), 2),
            "EMA50":     round(float(ema50), 2),
            "MACD":      round(float(macd_line.iloc[-1]), 2),
            "Signal":    round(float(signal_line.iloc[-1]), 2),
            "Histogram": round(float(histogram.iloc[-1]), 2),
        }
    except:
        return None

# ── Screener controls (above tabs) ─────────────────────────────────────────
st.markdown("### Nifty 50 Screener")
col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1,1,1,1,1])
with col_f1:
    rsi_min = st.slider("Min RSI", 0, 90, 15)
with col_f2:
    rsi_max = st.slider("Max RSI", 10, 90, 40)
with col_f3:
    setup_only = st.checkbox("EMA zone only", value=False, help="Price between EMA 20 and EMA 50")
with col_f4:
    bull_only = st.checkbox("Bullish trend only", value=False, help="EMA 20 > EMA 50")
with col_f5:
    run = st.button("▶ Run screener", type="primary", use_container_width=True)

if run:
    results = []
    progress = st.progress(0, text="Starting…")
    for i, (sym, meta) in enumerate(NIFTY50.items()):
        progress.progress((i+1)/len(NIFTY50), text=f"Fetching {sym}…")
        data = fetch_stock(sym)
        if data:
            ltp, ema20, ema50 = data["LTP"], data["EMA20"], data["EMA50"]
            ema_ok    = min(ema20,ema50) <= ltp <= max(ema20,ema50)
            bull      = ema20 > ema50
            macd_bull = data["Histogram"] > 0
            results.append({
                "Stock":     sym,
                "Sector":    meta["sector"],
                "LTP ₹":    data["LTP"],
                "Chg%":      data["Chg%"],
                "RSI":       data["RSI"],
                "EMA 20":    data["EMA20"],
                "EMA 50":    data["EMA50"],
                "MACD":      data["MACD"],
                "Signal":    data["Signal"],
                "Histogram": data["Histogram"],
                "EMA Zone":  "Yes" if ema_ok else "No",
                "Trend":     "Bull" if bull else "Bear",
                "MACD Bias": "Bull" if macd_bull else "Bear",
                "Lot":       meta["lot"],
            })
    progress.empty()
    if not results:
        st.warning("No data fetched. Try again.")
    else:
        df = pd.DataFrame(results)
        df = df[(df["RSI"] >= rsi_min) & (df["RSI"] <= rsi_max)]
        if setup_only: df = df[df["EMA Zone"] == "Yes"]
        if bull_only:  df = df[df["Trend"] == "Bull"]
        df = df.sort_values("RSI").reset_index(drop=True)
        df.index += 1
        m1,m2,m3,m4,m5 = st.columns(5)
        m1.metric("Screened", len(results))
        m2.metric("Matches",  len(df))
        m3.metric("EMA zone", len(df[df["EMA Zone"]=="Yes"]) if len(df) else 0)
        m4.metric("Bullish",  len(df[df["Trend"]=="Bull"]) if len(df) else 0)
        m5.metric("Avg RSI",  round(df["RSI"].mean(),1) if len(df) else "—")
        if df.empty:
            st.info("No stocks match the filters.")
        else:
            def color_rsi(val):
                if val < 20:   return "color:#185FA5;font-weight:600"
                elif val < 30: return "color:#1D9E75;font-weight:600"
                elif val < 40: return "color:#D98A1A;font-weight:600"
                elif val > 70: return "color:#E24B4A;font-weight:600"
                return ""
            def color_chg(val):  return "color:#1D9E75" if val>=0 else "color:#E24B4A"
            def color_hist(val): return "color:#1D9E75" if val>=0 else "color:#E24B4A"
            styled = df.style                .map(color_rsi,  subset=["RSI"])                .map(color_chg,  subset=["Chg%"])                .map(color_hist, subset=["Histogram"])                .format({"LTP ₹":"₹{:.2f}","Chg%":"{:+.2f}%","RSI":"{:.1f}",
                         "EMA 20":"₹{:.2f}","EMA 50":"₹{:.2f}",
                         "MACD":"{:.2f}","Signal":"{:.2f}","Histogram":"{:.2f}","Lot":"{:,}"})
            st.dataframe(styled, use_container_width=True, height=480)
            st.caption("RSI 14 · EMA 20/50 · MACD(12,26,9) · Yahoo Finance · Lot sizes Jun 2026 · Not financial advice")
            st.download_button("⬇ Download CSV", df.to_csv(index=False), "vedhi_screener.csv", "text/csv")

import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Vedhi Pulse", layout="wide", page_icon="📈")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,400;1,600&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"], p, span, div {
    font-family: 'Inter', sans-serif !important;
}
.vedhi-brand {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic;
    font-weight: 700;
    font-size: 46px;
    color: #1A1A18;
    letter-spacing: -1.5px;
    line-height: 1.1;
}
.vedhi-brand .pulse {
    color: #1D9E75;
}
.vedhi-sub {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 400;
    color: #999;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 6px;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #EAF3DE;
    color: #27500A;
    font-size: 10px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 8px;
}
.live-dot-c {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #1D9E75;
    display: inline-block;
    animation: blink 1.5s infinite;
}
@keyframes blink {0%,100%{opacity:1}50%{opacity:.2}}
.metric-card{background:#F7F7F5;border-radius:10px;padding:14px 18px;margin-bottom:8px}
.green{color:#1D9E75;font-weight:600}
.red{color:#E24B4A;font-weight:600}
.blue{color:#185FA5;font-weight:600}
.orange{color:#D85A30;font-weight:600}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:8px 0 20px">
  <div class="vedhi-brand">Vedhi <span class="pulse">Pulse</span></div>
  <div class="vedhi-sub">Nifty 50 Intelligence &nbsp;&middot;&nbsp; NSE India &nbsp;&middot;&nbsp; Live Market Data</div>
  <div class="live-badge"><span class="live-dot-c"></span>&nbsp;Live</div>
</div>
""", unsafe_allow_html=True)

# ── Nifty 50 Index Live Indicators ──────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_nifty_indicators():
    try:
        df = yf.download("^NSEI", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 55:
            return None
        close = df["Close"].squeeze()
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
        delta = close.diff()
        gain  = delta.where(delta>0,0).rolling(14).mean()
        loss  = (-delta.where(delta<0,0)).rolling(14).mean()
        rsi   = (100 - (100/(1+gain/loss.replace(0,1e-10)))).iloc[-1]
        ema12     = close.ewm(span=12, adjust=False).mean()
        ema26     = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal    = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal
        ltp  = close.iloc[-1]
        prev = close.iloc[-2]
        chg  = ltp - prev
        chgp = (chg/prev)*100
        return {
            "ltp":float(ltp), "chg":float(chg), "chgp":float(chgp),
            "rsi":round(float(rsi),1),
            "ema20":round(float(ema20),1),
            "ema50":round(float(ema50),1),
            "macd":round(float(macd_line.iloc[-1]),2),
            "signal":round(float(signal.iloc[-1]),2),
            "histogram":round(float(histogram.iloc[-1]),2),
        }
    except Exception as e:
        return None

nifty = fetch_nifty_indicators()

if nifty:
    st.markdown("### Nifty 50 — Live Technical Indicators")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    chg_sign = "+" if nifty["chg"] >= 0 else ""
    arrow    = "▲" if nifty["chg"] >= 0 else "▼"

    col1.metric(
        "Nifty 50",
        f"{nifty['ltp']:,.2f}",
        f"{arrow} {abs(nifty['chg']):.2f} ({abs(nifty['chgp']):.2f}%)"
    )
    rsi_label = "Oversold" if nifty["rsi"]<30 else "Value zone" if nifty["rsi"]<40 else "Neutral" if nifty["rsi"]<60 else "Elevated" if nifty["rsi"]<70 else "Overbought"
    col2.metric("RSI (14)", f"{nifty['rsi']}", rsi_label)
    col3.metric("EMA 20", f"{nifty['ema20']:,.1f}",
                "Price above" if nifty["ltp"] > nifty["ema20"] else "Price below")
    col4.metric("EMA 50", f"{nifty['ema50']:,.1f}",
                "Price above" if nifty["ltp"] > nifty["ema50"] else "Price below")
    col5.metric("MACD", f"{nifty['macd']:+.2f}",
                f"Signal {nifty['signal']:+.2f}")
    col6.metric("Histogram", f"{nifty['histogram']:+.2f}",
                "Bullish" if nifty["histogram"] >= 0 else "Bearish")

    st.caption(f"Auto-refreshes every 5 min | Source: Yahoo Finance | {pd.Timestamp.now().strftime('%d %b %Y %H:%M')} IST")
else:
    st.warning("Could not fetch Nifty 50 data — please refresh the page.")

st.divider()

# ── Nifty 50 tickers ─────────────────────────────────────────────────────────
NIFTY50 = {
    "ADANIENT":   {"sector":"Conglomerate", "lot":309},
    "ADANIPORTS": {"sector":"Ports",        "lot":475},
    "APOLLOHOSP": {"sector":"Healthcare",   "lot":125},
    "ASIANPAINT": {"sector":"Paint",        "lot":250},
    "AXISBANK":   {"sector":"Bank",         "lot":625},
    "BAJAJ-AUTO": {"sector":"Auto",         "lot":75},
    "BAJFINANCE": {"sector":"NBFC",         "lot":750},
    "BAJAJFINSV": {"sector":"NBFC",         "lot":250},
    "BEL":        {"sector":"Defence",      "lot":1425},
    "BPCL":       {"sector":"Energy",       "lot":1975},
    "BHARTIARTL": {"sector":"Telecom",      "lot":475},
    "BRITANNIA":  {"sector":"FMCG",         "lot":125},
    "CIPLA":      {"sector":"Pharma",       "lot":375},
    "COALINDIA":  {"sector":"Energy",       "lot":1350},
    "DIVISLAB":   {"sector":"Pharma",       "lot":100},
    "DRREDDY":    {"sector":"Pharma",       "lot":625},
    "EICHERMOT":  {"sector":"Auto",         "lot":100},
    "GRASIM":     {"sector":"Cement",       "lot":250},
    "HCLTECH":    {"sector":"IT",           "lot":350},
    "HDFCBANK":   {"sector":"Bank",         "lot":550},
    "HDFCLIFE":   {"sector":"Insurance",    "lot":1100},
    "HEROMOTOCO": {"sector":"Auto",         "lot":150},
    "HINDALCO":   {"sector":"Metal",        "lot":700},
    "HINDUNILVR": {"sector":"FMCG",         "lot":300},
    "ICICIBANK":  {"sector":"Bank",         "lot":700},
    "ITC":        {"sector":"FMCG",         "lot":1600},
    "INDUSINDBK": {"sector":"Bank",         "lot":700},
    "INFY":       {"sector":"IT",           "lot":400},
    "JSWSTEEL":   {"sector":"Metal",        "lot":675},
    "KOTAKBANK":  {"sector":"Bank",         "lot":2000},
    "LT":         {"sector":"Infra",        "lot":175},
    "M&M":        {"sector":"Auto",         "lot":200},
    "MARUTI":     {"sector":"Auto",         "lot":50},
    "NTPC":       {"sector":"PSU Power",    "lot":1500},
    "NESTLEIND":  {"sector":"FMCG",         "lot":500},
    "ONGC":       {"sector":"Energy",       "lot":2250},
    "POWERGRID":  {"sector":"PSU Power",    "lot":1900},
    "RELIANCE":   {"sector":"Conglomerate", "lot":500},
    "SBILIFE":    {"sector":"Insurance",    "lot":375},
    "SHRIRAMFIN": {"sector":"NBFC",         "lot":825},
    "SBIN":       {"sector":"PSU Bank",     "lot":750},
    "SUNPHARMA":  {"sector":"Pharma",       "lot":350},
    "TCS":        {"sector":"IT",           "lot":175},
    "TATACONSUM": {"sector":"FMCG",         "lot":550},
    "TATAMOTORS": {"sector":"Auto",         "lot":1425},
    "TATASTEEL":  {"sector":"Metal",        "lot":2750},
    "TECHM":      {"sector":"IT",           "lot":600},
    "TITAN":      {"sector":"Consumer",     "lot":175},
    "ULTRACEMCO": {"sector":"Cement",       "lot":50},
    "WIPRO":      {"sector":"IT",           "lot":3000},
}

# ── Indicator functions ───────────────────────────────────────────────────────
def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast   = series.ewm(span=fast, adjust=False).mean()
    ema_slow   = series.ewm(span=slow, adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line= macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram

# ── Fetch one stock ───────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_stock(symbol):
    try:
        df = yf.download(f"{symbol}.NS", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 55:
            return None
        close = df["Close"].squeeze()
        ema20 = calc_ema(close, 20).iloc[-1]
        ema50 = calc_ema(close, 50).iloc[-1]
        rsi   = calc_rsi(close).iloc[-1]
        macd_line, signal_line, histogram = calc_macd(close)
        ltp   = close.iloc[-1]
        prev  = close.iloc[-2]
        chg   = ltp - prev
        chg_pct = (chg / prev) * 100
        return {
            "LTP":       round(float(ltp), 2),
            "Change":    round(float(chg), 2),
            "Chg%":      round(float(chg_pct), 2),
            "RSI":       round(float(rsi), 1),
            "EMA20":     round(float(ema20), 2),
            "EMA50":     round(float(ema50), 2),
            "MACD":      round(float(macd_line.iloc[-1]), 2),
            "Signal":    round(float(signal_line.iloc[-1]), 2),
            "Histogram": round(float(histogram.iloc[-1]), 2),
        }
    except:
        return None

# ── Indicator Glossary ────────────────────────────────────────────────────────
st.divider()
with st.expander("📖 Indicator Glossary — click to open"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
**📌 LTP ₹ — Last Traded Price**
Current market price of the stock on NSE.

---
**📌 Chg% — Daily Change**
Percentage change from yesterday's closing price.
🟢 Positive = stock rose  ·  🔴 Negative = stock fell

---
**📌 RSI (14-day)**
Momentum indicator 0–100.
- < 30 🔵 Oversold — may bounce, good entry
- 30–40 🟢 Value zone — strong swing entry
- 40–60 ⚪ Neutral — no clear signal
- 60–70 🟡 Elevated — caution on new buys
- > 70 🔴 Overbought — may correct

---
**📌 EMA 20 — 20-day Exponential Moving Average**
Short-term trend. Price above = bullish. Price below = bearish.

---
**📌 EMA 50 — 50-day Exponential Moving Average**
Medium-term trend.
- Golden Cross → EMA 20 above EMA 50 = strong buy signal
- Death Cross → EMA 20 below EMA 50 = sell signal
        """)
    with col_b:
        st.markdown("""
**📌 EMA Zone**
Price is between EMA 20 and EMA 50 — the classic pullback zone.
- ✅ Yes = potential entry point
- ❌ No = outside zone

---
**📌 Trend**
- ▲ Bull = EMA 20 above EMA 50 (uptrend)
- ▼ Bear = EMA 20 below EMA 50 (downtrend)

---
**📌 MACD (12, 26, 9)**
MACD Line = EMA 12 minus EMA 26.
Positive = bullish momentum · Negative = bearish.

---
**📌 Signal Line**
9-day EMA of MACD.
- MACD crosses above Signal → 🟢 Buy
- MACD crosses below Signal → 🔴 Sell

---
**📌 Histogram**
MACD minus Signal. Shows momentum strength.
- 🟢 Positive = bullish · 🔴 Negative = bearish

---
**📌 MACD Bias**
Bull = Histogram positive · Bear = Histogram negative

---
**📌 Lot**
NSE F&O lot size — shares per contract. Verified Jun 2026.
        """)
    st.caption("RSI(14) · EMA(20,50) · MACD(12,26,9) · Yahoo Finance · Not financial advice")
