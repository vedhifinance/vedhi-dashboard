import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Vedhi Trading Dashboard", layout="wide", page_icon="📈")

st.markdown("""
<style>
.metric-card{background:#F7F7F5;border-radius:10px;padding:14px 18px;margin-bottom:8px}
.green{color:#1D9E75;font-weight:600}
.red{color:#E24B4A;font-weight:600}
.blue{color:#185FA5;font-weight:600}
.orange{color:#D85A30;font-weight:600}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📈 Vedhi Trading Dashboard")
st.markdown("**Nifty 50 Strategy Hub** &nbsp;|&nbsp; NSE India &nbsp;|&nbsp; Live Data via Yahoo Finance")
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

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📈 Nifty 50 Swing Strategy",
    "📊 Nifty 50 Swing-Covered Strategy",
    "🎯 BEL Long-Covered Strategy",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SWING SCREENER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Nifty 50 Swing Screener")
    st.markdown("Live RSI · EMA 20 · EMA 50 · MACD · Ranked by lowest RSI · Lot sizes verified Jun 2026")

    # Sidebar-style filters inside tab
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        rsi_min = st.slider("Min RSI", 0, 90, 15)
    with col_f2:
        rsi_max = st.slider("Max RSI", 10, 90, 40)
    with col_f3:
        setup_only = st.checkbox("EMA zone only", value=False,
                                  help="Price between EMA 20 and EMA 50")
    with col_f4:
        bull_only = st.checkbox("Bullish trend only", value=False,
                                 help="EMA 20 > EMA 50")

    run = st.button("▶ Run screener", type="primary", use_container_width=False)

    if run:
        results = []
        progress = st.progress(0, text="Starting…")

        for i, (sym, meta) in enumerate(NIFTY50.items()):
            progress.progress((i+1)/len(NIFTY50), text=f"Fetching {sym}…")
            data = fetch_stock(sym)
            if data:
                ltp, ema20, ema50 = data["LTP"], data["EMA20"], data["EMA50"]
                ema_ok  = min(ema20,ema50) <= ltp <= max(ema20,ema50)
                bull    = ema20 > ema50
                macd_bull = data["Histogram"] > 0
                results.append({
                    "Stock":    sym,
                    "Sector":   meta["sector"],
                    "LTP ₹":   data["LTP"],
                    "Chg%":     data["Chg%"],
                    "RSI":      data["RSI"],
                    "EMA 20":   data["EMA20"],
                    "EMA 50":   data["EMA50"],
                    "MACD":     data["MACD"],
                    "Signal":   data["Signal"],
                    "Histogram":data["Histogram"],
                    "EMA Zone": "✓ Yes" if ema_ok else "No",
                    "Trend":    "▲ Bull" if bull else "▼ Bear",
                    "MACD Bias":"▲ Bull" if macd_bull else "▼ Bear",
                    "Lot":      meta["lot"],
                })

        progress.empty()

        if not results:
            st.warning("No data fetched. Please try again.")
        else:
            df = pd.DataFrame(results)

            # Apply filters
            df = df[(df["RSI"] >= rsi_min) & (df["RSI"] <= rsi_max)]
            if setup_only:
                df = df[df["EMA Zone"] == "✓ Yes"]
            if bull_only:
                df = df[df["Trend"] == "▲ Bull"]

            df = df.sort_values("RSI").reset_index(drop=True)
            df.index += 1

            # Summary metrics
            st.divider()
            m1,m2,m3,m4,m5 = st.columns(5)
            m1.metric("Stocks screened", len(results))
            m2.metric("Matches found",   len(df))
            m3.metric("In EMA zone",     len(df[df["EMA Zone"]=="✓ Yes"]))
            m4.metric("Bullish trend",   len(df[df["Trend"]=="▲ Bull"]))
            m5.metric("Avg RSI",         round(df["RSI"].mean(),1) if len(df) else "—")

            st.divider()

            if df.empty:
                st.info("No stocks match the current filter settings.")
            else:
                # Color RSI column
                def color_rsi(val):
                    if val < 20:   return "color:#185FA5;font-weight:600"
                    elif val < 30: return "color:#1D9E75;font-weight:600"
                    elif val < 40: return "color:#D98A1A;font-weight:600"
                    elif val > 70: return "color:#E24B4A;font-weight:600"
                    return ""

                def color_chg(val):
                    return "color:#1D9E75" if val >= 0 else "color:#E24B4A"

                def color_hist(val):
                    return "color:#1D9E75" if val >= 0 else "color:#E24B4A"

                styled = df.style\
                    .map(color_rsi, subset=["RSI"])\
                    .map(color_chg, subset=["Chg%"])\
                    .map(color_hist, subset=["Histogram"])\
                    .format({
                        "LTP ₹":    "₹{:.2f}",
                        "Chg%":     "{:+.2f}%",
                        "RSI":      "{:.1f}",
                        "EMA 20":   "₹{:.2f}",
                        "EMA 50":   "₹{:.2f}",
                        "MACD":     "{:.2f}",
                        "Signal":   "{:.2f}",
                        "Histogram":"{:.2f}",
                        "Lot":      "{:,}",
                    })

                st.dataframe(styled, use_container_width=True, height=500)
                st.caption("RSI 14 · EMA 20/50 · MACD(12,26,9) · Data: Yahoo Finance · Lot sizes: Jun 2026 · Not financial advice")

                # Export
                csv = df.to_csv(index=False)
                st.download_button("⬇ Download CSV", csv, "vedhi_swing_screener.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SWING COVERED STRATEGY (placeholder)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Nifty 50 Swing-Covered Strategy")
    st.info("This section is coming soon. Tell me what to build here!")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — BEL COVERED CALL (placeholder)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### BEL Long-Covered Strategy")
    st.info("This section is coming soon. Tell me what to build here!")
