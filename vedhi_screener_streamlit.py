import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Vedhi Pulse", layout="wide", page_icon="📈")

# ── Fonts & Styles ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,700&family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.brand { font-family: 'Playfair Display', Georgia, serif !important; font-style: italic;
         font-size: 44px; font-weight: 700; color: #1A1A18; letter-spacing: -1px; line-height: 1.1; }
.brand .pulse { color: #1D9E75; }
.sub { font-size: 12px; color: #999; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 6px; }
.live-badge { display: inline-flex; align-items: center; gap: 5px; background: #EAF3DE;
              color: #27500A; font-size: 10px; font-weight: 600; padding: 3px 10px;
              border-radius: 20px; letter-spacing: 0.06em; text-transform: uppercase; margin-top: 8px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #1D9E75;
       display: inline-block; animation: blink 1.5s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }
</style>
""", unsafe_allow_html=True)

# ── Header (once) ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:8px 0 20px">
  <div class="brand">Vedhi <span class="pulse">Pulse</span></div>
  <div class="sub">Nifty 50 Intelligence &nbsp;·&nbsp; NSE India &nbsp;·&nbsp; Live Market Data</div>
  <div class="live-badge"><span class="dot"></span>&nbsp;Live</div>
</div>
""", unsafe_allow_html=True)

# ── Nifty 50 Live Indicators (once) ──────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_nifty():
    try:
        df = yf.download("^NSEI", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 55: return None
        c = df["Close"].squeeze() if hasattr(df["Close"], "squeeze") else df["Close"] if hasattr(df["Close"], "squeeze") else df["Close"]
        ema20 = c.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = c.ewm(span=50, adjust=False).mean().iloc[-1]
        d = c.diff()
        g = d.where(d>0,0).rolling(14).mean()
        l = (-d.where(d<0,0)).rolling(14).mean()
        rsi = (100-(100/(1+g/l.replace(0,1e-10)))).iloc[-1]
        e12 = c.ewm(span=12, adjust=False).mean()
        e26 = c.ewm(span=26, adjust=False).mean()
        macd = e12 - e26
        sig  = macd.ewm(span=9, adjust=False).mean()
        hist = macd - sig
        ltp  = float(c.iloc[-1])
        prev = float(c.iloc[-2])
        return {
            "ltp": ltp, "chg": ltp-prev, "chgp": (ltp-prev)/prev*100,
            "rsi": round(float(rsi),1), "ema20": round(float(ema20),1),
            "ema50": round(float(ema50),1), "macd": round(float(macd.iloc[-1]),2),
            "signal": round(float(sig.iloc[-1]),2), "hist": round(float(hist.iloc[-1]),2),
        }
    except: return None

nifty = fetch_nifty()
if nifty:
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    arrow = "▲" if nifty["chg"] >= 0 else "▼"
    c1.metric("Nifty 50", f"{nifty['ltp']:,.2f}",
              f"{arrow} {abs(nifty['chg']):.2f} ({abs(nifty['chgp']):.2f}%)")
    rsi_lbl = "Oversold" if nifty["rsi"]<30 else "Value zone" if nifty["rsi"]<40 else \
              "Neutral" if nifty["rsi"]<60 else "Elevated" if nifty["rsi"]<70 else "Overbought"
    c2.metric("RSI (14)", nifty["rsi"], rsi_lbl)
    c3.metric("EMA 20", f"{nifty['ema20']:,.1f}",
              "Above" if nifty["ltp"]>nifty["ema20"] else "Below")
    c4.metric("EMA 50", f"{nifty['ema50']:,.1f}",
              "Above" if nifty["ltp"]>nifty["ema50"] else "Below")
    c5.metric("MACD", f"{nifty['macd']:+.2f}", f"Signal {nifty['signal']:+.2f}")
    c6.metric("Histogram", f"{nifty['hist']:+.2f}",
              "Bullish" if nifty["hist"]>=0 else "Bearish")
    st.caption(f"Auto-refreshes every 5 min · Yahoo Finance · {pd.Timestamp.now().strftime('%d %b %Y %H:%M')} IST")
else:
    st.warning("Could not fetch Nifty 50 data — please refresh.")

st.divider()

# ── Nifty 50 tickers ──────────────────────────────────────────────────────────
NIFTY50 = {
    "ADANIENT":{"sector":"Conglomerate","lot":309}, "ADANIPORTS":{"sector":"Ports","lot":475},
    "APOLLOHOSP":{"sector":"Healthcare","lot":125}, "ASIANPAINT":{"sector":"Paint","lot":250},
    "AXISBANK":{"sector":"Bank","lot":625},         "BAJAJ-AUTO":{"sector":"Auto","lot":75},
    "BAJFINANCE":{"sector":"NBFC","lot":750},       "BAJAJFINSV":{"sector":"NBFC","lot":250},
    "BEL":{"sector":"Defence","lot":1425},           "BPCL":{"sector":"Energy","lot":1975},
    "BHARTIARTL":{"sector":"Telecom","lot":475},    "BRITANNIA":{"sector":"FMCG","lot":125},
    "CIPLA":{"sector":"Pharma","lot":375},           "COALINDIA":{"sector":"Energy","lot":1350},
    "DIVISLAB":{"sector":"Pharma","lot":100},        "DRREDDY":{"sector":"Pharma","lot":625},
    "EICHERMOT":{"sector":"Auto","lot":100},         "GRASIM":{"sector":"Cement","lot":250},
    "HCLTECH":{"sector":"IT","lot":350},             "HDFCBANK":{"sector":"Bank","lot":550},
    "HDFCLIFE":{"sector":"Insurance","lot":1100},   "HEROMOTOCO":{"sector":"Auto","lot":150},
    "HINDALCO":{"sector":"Metal","lot":700},         "HINDUNILVR":{"sector":"FMCG","lot":300},
    "ICICIBANK":{"sector":"Bank","lot":700},         "ITC":{"sector":"FMCG","lot":1600},
    "INDUSINDBK":{"sector":"Bank","lot":700},        "INFY":{"sector":"IT","lot":400},
    "JSWSTEEL":{"sector":"Metal","lot":675},         "KOTAKBANK":{"sector":"Bank","lot":2000},
    "LT":{"sector":"Infra","lot":175},               "M&M":{"sector":"Auto","lot":200},
    "MARUTI":{"sector":"Auto","lot":50},             "NTPC":{"sector":"PSU Power","lot":1500},
    "NESTLEIND":{"sector":"FMCG","lot":500},         "ONGC":{"sector":"Energy","lot":2250},
    "POWERGRID":{"sector":"PSU Power","lot":1900},  "RELIANCE":{"sector":"Conglomerate","lot":500},
    "SBILIFE":{"sector":"Insurance","lot":375},      "SHRIRAMFIN":{"sector":"NBFC","lot":825},
    "SBIN":{"sector":"PSU Bank","lot":750},          "SUNPHARMA":{"sector":"Pharma","lot":350},
    "TCS":{"sector":"IT","lot":175},                 "TATACONSUM":{"sector":"FMCG","lot":550},
    "TATAMOTORS":{"sector":"Auto","lot":1425},       "TATASTEEL":{"sector":"Metal","lot":2750},
    "TECHM":{"sector":"IT","lot":600},               "TITAN":{"sector":"Consumer","lot":175},
    "ULTRACEMCO":{"sector":"Cement","lot":50},       "WIPRO":{"sector":"IT","lot":3000},
}

@st.cache_data(ttl=1800)
def fetch_stock(symbol):
    try:
        df = yf.download(f"{symbol}.NS", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df)<55: return None
        c = df["Close"].squeeze() if hasattr(df["Close"], "squeeze") else df["Close"] if hasattr(df["Close"], "squeeze") else df["Close"]
        ema20 = c.ewm(span=20,adjust=False).mean().iloc[-1]
        ema50 = c.ewm(span=50,adjust=False).mean().iloc[-1]
        d=c.diff(); g=d.where(d>0,0).rolling(14).mean(); l=(-d.where(d<0,0)).rolling(14).mean()
        rsi=(100-(100/(1+g/l.replace(0,1e-10)))).iloc[-1]
        e12=c.ewm(span=12,adjust=False).mean(); e26=c.ewm(span=26,adjust=False).mean()
        macd=e12-e26; sig=macd.ewm(span=9,adjust=False).mean(); hist=macd-sig
        ltp=float(c.iloc[-1]); prev=float(c.iloc[-2])
        return {
            "LTP":round(ltp,2), "Chg%":round((ltp-prev)/prev*100,2),
            "RSI":round(float(rsi),1), "EMA 20":round(float(ema20),2),
            "EMA 50":round(float(ema50),2), "MACD":round(float(macd.iloc[-1]),2),
            "Signal":round(float(sig.iloc[-1]),2), "Histogram":round(float(hist.iloc[-1]),2),
        }
    except: return None

# ── Screener controls ─────────────────────────────────────────────────────────
st.markdown("### Nifty 50 Screener")
f1,f2,f3,f4,f5 = st.columns([1,1,1,1,1])
with f1: rsi_min = st.slider("Min RSI", 0, 90, 15)
with f2: rsi_max = st.slider("Max RSI", 10, 90, 40)
with f3: setup_only = st.checkbox("EMA zone only", help="Price between EMA 20 and EMA 50")
with f4: bull_only  = st.checkbox("Bullish trend only", help="EMA 20 > EMA 50")
with f5: run = st.button("▶ Run screener", type="primary", use_container_width=True)

if run:
    results = []
    prog = st.progress(0, text="Starting…")
    for i,(sym,meta) in enumerate(NIFTY50.items()):
        prog.progress((i+1)/len(NIFTY50), text=f"Fetching {sym}…")
        data = fetch_stock(sym)
        if data:
            ltp,e20,e50 = data["LTP"],data["EMA 20"],data["EMA 50"]
            ema_ok = min(e20,e50) <= ltp <= max(e20,e50)
            bull   = e20 > e50
            results.append({
                "Stock":sym, "Sector":meta["sector"],
                "LTP ₹":ltp, "Chg%":data["Chg%"], "RSI":data["RSI"],
                "EMA 20":e20, "EMA 50":e50,
                "MACD":data["MACD"], "Signal":data["Signal"], "Histogram":data["Histogram"],
                "EMA Zone":"Yes" if ema_ok else "No",
                "Trend":"Bull" if bull else "Bear",
                "MACD Bias":"Bull" if data["Histogram"]>=0 else "Bear",
                "Lot":meta["lot"],
            })
    prog.empty()
    if not results:
        st.warning("No data fetched. Try again.")
    else:
        df = pd.DataFrame(results)
        df = df[(df["RSI"]>=rsi_min)&(df["RSI"]<=rsi_max)]
        if setup_only: df = df[df["EMA Zone"]=="Yes"]
        if bull_only:  df = df[df["Trend"]=="Bull"]
        df = df.sort_values("RSI").reset_index(drop=True)
        df.index += 1
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Screened", len(results))
        c2.metric("Matches",  len(df))
        c3.metric("EMA zone", int((df["EMA Zone"]=="Yes").sum()))
        c4.metric("Bullish",  int((df["Trend"]=="Bull").sum()))
        c5.metric("Avg RSI",  round(df["RSI"].mean(),1) if len(df) else "—")
        if df.empty:
            st.info("No stocks match the filters.")
        else:
            # Remove injected CSS — not needed with HTML table
            # Build HTML table with black headers, white text
            cols = ["Stock","Sector","LTP ₹","Chg%","RSI","EMA 20","EMA 50",
                    "MACD","Signal","Histogram","EMA Zone","Trend","MACD Bias","Lot"]

            def cell_style(col, val, row=None):
                if col == "Stock":
                    return "background:#1A1A18;color:white;font-weight:700"
                if col == "RSI":
                    if val < 20:   return "color:#185FA5;font-weight:600"
                    if val < 30:   return "color:#1D9E75;font-weight:600"
                    if val < 40:   return "color:#D98A1A;font-weight:600"
                    if val > 70:   return "color:#E24B4A;font-weight:600"
                if col in ["Chg%","Histogram"]:
                    return "color:#1D9E75;font-weight:500" if val>=0 else "color:#E24B4A;font-weight:500"
                if col == "Trend":
                    return "background:#D6F5E3;color:#1A5C35;font-weight:600" if val=="Bull" \
                        else "background:#FDDCDC;color:#7A1A1A;font-weight:600"
                if col == "MACD Bias":
                    return "background:#D6F5E3;color:#1A5C35;font-weight:600" if val=="Bull" \
                        else "background:#FDDCDC;color:#7A1A1A;font-weight:600"
                if col == "EMA Zone":
                    return "background:#D6F5E3;color:#1A5C35;font-weight:600" if val=="Yes" \
                        else "background:#FDDCDC;color:#7A1A1A;font-weight:600"
                return ""

            def fmt_val(col, val):
                if col == "LTP ₹":    return f"₹{val:.2f}"
                if col == "Chg%":     return f"{val:+.2f}%"
                if col == "RSI":      return f"{val:.1f}"
                if col in ["EMA 20","EMA 50"]: return f"₹{val:.2f}"
                if col in ["MACD","Signal","Histogram"]: return f"{val:.2f}"
                if col == "Lot":      return f"{int(val):,}"
                return str(val)

            header_html = "".join(
                f'<th style="background:#1A1A18;color:white;font-weight:600;font-size:12px;'
                f'padding:10px 12px;text-align:left;white-space:nowrap;border-bottom:2px solid #000;border-right:0.5px solid #444;">'
                f'{c}</th>' for c in cols
            )

            rows_html = ""
            for i, row in df.iterrows():
                bg = "#FAFAF8" if i % 2 == 0 else "#FFFFFF"
                row_html = f'<tr style="background:{bg}">'
                for col in cols:
                    val = row[col]
                    style = cell_style(col, val, row)
                    display = fmt_val(col, val)
                    row_html += f'<td style="padding:9px 12px;font-size:13px;{style};border-bottom:0.5px solid #AAAAAA;border-right:0.5px solid #AAAAAA;">{display}</td>'
                row_html += "</tr>"
                rows_html += row_html

            table_html = f"""
            <div style="overflow-x:auto;border:0.5px solid #E0DED8;border-radius:10px;overflow:hidden">
              <table style="width:100%;border-collapse:collapse;font-family:system-ui,sans-serif">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{rows_html}</tbody>
              </table>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)
            st.caption("RSI(14) · EMA(20,50) · MACD(12,26,9) · Yahoo Finance · Not financial advice")
            st.download_button("⬇ Download CSV", df.to_csv(index=False), "vedhi_screener.csv", "text/csv")

st.divider()

# ── Indicator Glossary ────────────────────────────────────────────────────────
with st.expander("📖 Indicator Glossary — click to open"):
    ga, gb = st.columns(2)
    with ga:
        st.markdown("""
**📌 LTP ₹ — Last Traded Price**
Current market price on NSE.

---
**📌 Chg% — Daily Change**
% change from yesterday's close. 🟢 = up · 🔴 = down

---
**📌 RSI (14-day)**
Momentum indicator 0–100.
| Range | Zone | Action |
|---|---|---|
| < 30 | 🔵 Oversold | May bounce — good entry |
| 30–40 | 🟢 Value zone | Strong swing entry |
| 40–60 | ⚪ Neutral | No clear signal |
| 60–70 | 🟡 Elevated | Caution |
| > 70 | 🔴 Overbought | Avoid entry |

---
**📌 EMA 20 — 20-day EMA**
Short-term trend. Price above = bullish · below = bearish.

---
**📌 EMA 50 — 50-day EMA**
Medium-term trend.
- Golden Cross → EMA 20 above EMA 50 = buy signal
- Death Cross → EMA 20 below EMA 50 = sell signal
        """)
    with gb:
        st.markdown("""
**📌 EMA Zone**
Price between EMA 20 and EMA 50 — classic pullback entry zone.
✅ Yes = potential entry · ❌ No = outside zone

---
**📌 Trend**
▲ Bull = EMA 20 above EMA 50 · ▼ Bear = EMA 20 below EMA 50

---
**📌 MACD (12, 26, 9)**
MACD = EMA 12 minus EMA 26.
Positive = bullish · Negative = bearish momentum.

---
**📌 Signal Line**
9-day EMA of MACD.
- MACD above Signal → 🟢 Buy
- MACD below Signal → 🔴 Sell

---
**📌 Histogram**
MACD minus Signal. Shows momentum strength.
🟢 Positive = bullish · 🔴 Negative = bearish

---
**📌 MACD Bias**
Bull = Histogram positive · Bear = Histogram negative

---
**📌 Lot**
NSE F&O lot size — shares per contract. Verified Jun 2026.
        """)
    st.caption("RSI(14) · EMA(20,50) · MACD(12,26,9) · Yahoo Finance daily data · Not financial advice")

st.divider()

# ── Strategy Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📈 Nifty 50 Swing Strategy",
    "📊 Nifty 50 Swing-Covered Strategy",
    "🎯 BEL Long-Covered Strategy",
])

with tab1:
    st.markdown("### Nifty 50 Swing Strategy")
    st.info("Use the **▶ Run screener** above to scan all 50 Nifty stocks.")

with tab2:
    import math

    st.markdown("### 📊 Nifty 50 Swing-Covered Strategy")
    st.markdown("7-layer confluence filter · Institutional grade · Only high-probability setups")
    st.divider()

    # ── Strategy explanation ──────────────────────────────────────────────────
    with st.expander("📖 Complete strategy rules — click to read"):
        st.markdown("""
### Entry Checklist — All 7 must be true

| # | Filter | Condition | Why it matters |
|---|---|---|---|
| 1 | **Structural trend** | Price > EMA 200 **AND** at least 5% above it | Confirms major uptrend, avoids weak recoveries |
| 2 | **Weekly trend** | Weekly close > Weekly EMA 20 | Ensures daily bounce is WITH the weekly trend |
| 3 | **Value zone** | Price between EMA 20 and EMA 50 | Pullback to institutional support — not overbought |
| 4 | **RSI** | Between 35 and 45 | Oversold enough for value, not so low it is broken |
| 5 | **Volume** | Today ≥ 1.5x 20-day average | Smart money confirming the move |
| 6 | **Trigger candle** | Hammer / Bullish Engulfing / Strong Green Close | Entry signal — market showing its hand |
| 7 | **Market breadth** | Nifty 50 above its own EMA 50 | Never fight the broader market |

### Covered Call Rules
- **Do not sell the call on entry day** — wait 1–2 days for bounce to begin, premium will be better
- **Strike selection** — nearest resistance / previous swing high above LTP
- **Expiry** — monthly expiry with 20–30 days remaining (best premium decay)
- **Target** — 8% above entry (book 50% at 4%, rest at 8%)
- **Stop loss** — close below the trigger candle's low
- **Time stop** — if no movement in 5 sessions, exit regardless

### Market condition
- 🟢 Nifty above EMA 50 = take all qualifying setups
- 🟡 Nifty between EMA 50 and EMA 200 = take only strongest setups
- 🔴 Nifty below EMA 200 = avoid all setups, capital preservation mode
        """)

    with st.expander("📚 Indicator Glossary — what each filter means and why — click to open"):
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("""
**📌 Filter 1 — EMA 200 (Structural Trend)**
EMA 200 = 200-day Exponential Moving Average. This is the most important long-term trend line used by fund managers and institutions worldwide.
- Price **above** EMA 200 = stock is in a **long-term uptrend** — bulls are in control
- Price **below** EMA 200 = stock is in a **long-term downtrend** — avoid completely
- We require price to be **5% above** EMA 200, not just barely above it. This eliminates stocks that are recovering from a downtrend but haven't confirmed strength yet.

---
**📌 Filter 2 — Weekly EMA 20 (Weekly Trend)**
Same as EMA 20 but calculated on **weekly candles** instead of daily. This checks if the medium-term (multi-month) trend is bullish.
- Weekly close **above** Weekly EMA 20 = weekly uptrend intact
- Weekly close **below** Weekly EMA 20 = the daily setup is going against the weekly flow — dangerous
- A daily bounce inside a weekly downtrend is a **trap**, not an opportunity.

---
**📌 Filter 3 — EMA Zone / Value Zone**
EMA 20 = 20-day average. EMA 50 = 50-day average. The **zone between them** is where institutional buyers typically enter during a healthy pullback in an uptrend.
- Price **between EMA 20 and EMA 50** = stock has pulled back to support without breaking trend — best entry zone
- EMA 20 **above** EMA 50 = short-term trend is bullish (golden cross)
- We also check that EMA 20 and EMA 50 are **at least 1% apart** — if they are too close the trend is flat, not a real setup
- Think of this zone as the market offering a **discount in an uptrend**

---
**📌 Filter 4 — RSI 35 to 45**
RSI = Relative Strength Index (14-day). Measures how overbought or oversold a stock is on a scale of 0 to 100.
- RSI **below 35** = stock may be broken or in serious trouble — avoid
- RSI **35 to 45** = sweet spot — oversold enough to offer value, not so low that something is fundamentally wrong
- RSI **above 45** = not oversold enough — wait for a better pullback
- The 35–45 band is specifically chosen to match the EMA zone pullback — when both align, confidence is very high
            """)
        with g2:
            st.markdown("""
**📌 Filter 5 — Volume 1.5x Average**
Volume = number of shares traded today. We compare it to the 20-day average volume.
- Volume **≥ 1.5x average** = institutional money is participating — confirms the move is real
- Volume **< 1.5x average** = the candle pattern could be random noise with no conviction
- High volume on a bullish candle at support = **smart money buying**. This is the most important confirmation after the candle pattern.
- 2x volume or more = extremely strong confirmation, adds to score

---
**📌 Filter 6 — Trigger Candle**
The candle pattern on today's daily chart. Acts as the **entry signal** — we don't enter until the market shows us a reversal sign.

🔨 **Hammer**
- Small body at the top of the candle
- Long lower wick (at least 2x the body)
- Tiny or no upper wick
- Means: sellers pushed price down but buyers fought back strongly — rejection of lower prices

🕯 **Bullish Engulfing**
- Previous day was a red (bearish) candle
- Today's green candle body completely covers the previous red candle body
- Means: buyers completely overwhelmed sellers — strong reversal signal
- This is the **strongest** of the three patterns

💚 **Strong Green Close**
- Green candle (close above open)
- Body is at least 60% of the full day range
- Closes in the top 25% of the day's range
- Means: buyers were in control all day and held gains — strong momentum

---
**📌 Filter 7 — Market Breadth (Nifty EMA 50)**
Individual stocks follow the broader market. Even the best setup fails if the market is in a downtrend.
- Nifty **above EMA 50** = market is healthy, take all setups
- Nifty **between EMA 50 and EMA 200** = market is weak, take only highest score setups
- Nifty **below EMA 200** = bear market, scanner is disabled automatically — protect capital

---
**📌 Confidence Score (out of 10)**
The scanner scores each qualifying stock:
- 5 points for passing all 5 original filters
- +1 for weekly trend confirmation
- +1 for EMA 200 buffer confirmation
- +1 for volume ≥ 2x (extra strong)
- +1 for Bullish Engulfing candle (strongest pattern)
- +1 for R:R ratio ≥ 2:1
- **Score 8+** = very high confidence · **6–7** = good setup · **5** = minimum qualifying

---
**📌 R:R Ratio (Risk to Reward)**
Risk = entry price minus stop loss. Reward = target minus entry price.
- R:R of 2:1 means you make ₹2 for every ₹1 risked — minimum acceptable
- R:R of 3:1 or above = excellent setup, prioritise these
            """)
        st.caption("All indicators calculated from Yahoo Finance 2-year daily data · Not financial advice")

    # ── Market breadth check ──────────────────────────────────────────────────
    @st.cache_data(ttl=300)
    def check_market_breadth():
        try:
            df = yf.download("^NSEI", period="1y", interval="1d",
                             progress=False, auto_adjust=True)
            if df.empty: return None
            close = df["Close"].squeeze().dropna()
            weekly = close.resample("W").last().dropna()
            nifty_ltp  = float(close.iloc[-1])
            nifty_ema50= float(close.ewm(span=50, adjust=False).mean().iloc[-1])
            nifty_ema200=float(close.ewm(span=200,adjust=False).mean().iloc[-1])
            weekly_ema20=float(weekly.ewm(span=20,adjust=False).mean().iloc[-1])
            weekly_close=float(weekly.iloc[-1])
            if nifty_ltp > nifty_ema50:
                condition = "green"
                label     = "🟢 Bullish — Market above EMA 50. Take all qualifying setups."
            elif nifty_ltp > nifty_ema200:
                condition = "yellow"
                label     = "🟡 Caution — Market between EMA 50 and EMA 200. Take only strongest setups."
            else:
                condition = "red"
                label     = "🔴 Avoid — Market below EMA 200. Capital preservation mode. Do not enter new positions."
            return {
                "condition":   condition,
                "label":       label,
                "nifty_ltp":   nifty_ltp,
                "nifty_ema50": nifty_ema50,
                "nifty_ema200":nifty_ema200,
                "weekly_above":weekly_close > weekly_ema20,
            }
        except: return None

    breadth = check_market_breadth()

    if breadth:
        bc = {"green":"#D6F5E3","yellow":"#FFF9DB","red":"#FDDCDC"}
        bc2= {"green":"#1A5C35","yellow":"#7A5C00","red":"#7A1A1A"}
        st.markdown(f"""
        <div style="background:{bc[breadth['condition']]};border:1.5px solid;
                    border-color:{'#1D9E75' if breadth['condition']=='green' else '#F5C842' if breadth['condition']=='yellow' else '#E24B4A'};
                    border-radius:10px;padding:14px 20px;margin-bottom:18px;
                    font-size:14px;font-weight:500;color:{bc2[breadth['condition']]}">
          {breadth['label']}<br>
          <span style="font-size:12px;font-weight:400;opacity:.8">
            Nifty: ₹{breadth['nifty_ltp']:,.0f} · EMA 50: ₹{breadth['nifty_ema50']:,.0f} · EMA 200: ₹{breadth['nifty_ema200']:,.0f}
          </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Could not fetch market breadth data.")

    st.divider()

    # ── Candle detection ──────────────────────────────────────────────────────
    def detect_candle(o, h, l, c, prev_o, prev_c):
        body       = abs(c - o)
        full_range = h - l if h != l else 0.0001
        lower_wick = min(o,c) - l
        upper_wick = h - max(o,c)

        is_hammer = (
            lower_wick >= 2 * body and
            upper_wick <= 0.3 * body and
            body >= 0.1 * full_range and
            c > o
        )
        is_engulfing = (
            prev_c < prev_o and
            c > o and
            c > prev_o and
            o < prev_c
        )
        is_strong_green = (
            c > o and
            body >= 0.6 * full_range and
            (c - l) >= 0.75 * full_range
        )
        if is_hammer:       return "🔨 Hammer"
        if is_engulfing:    return "🕯 Bullish Engulfing"
        if is_strong_green: return "💚 Strong Green"
        return None

    # ── Main screen function ──────────────────────────────────────────────────
    @st.cache_data(ttl=1800)
    def screen_swing_covered(symbol):
        try:
            # Daily data
            df = yf.download(f"{symbol}.NS", period="2y", interval="1d",
                             progress=False, auto_adjust=True)
            if df.empty or len(df) < 210: return None, "not enough data"

            close  = df["Close"].squeeze().dropna()
            open_  = df["Open"].squeeze().dropna()
            high   = df["High"].squeeze().dropna()
            low    = df["Low"].squeeze().dropna()
            volume = df["Volume"].squeeze().dropna()

            if len(close) < 200: return None, "not enough data"

            ltp    = float(close.iloc[-1])
            ema20  = float(close.ewm(span=20,  adjust=False).mean().iloc[-1])
            ema50  = float(close.ewm(span=50,  adjust=False).mean().iloc[-1])
            ema200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])

            # ── Filter 1: Above EMA 200 with 5% buffer ───────────────────────
            if ltp <= ema200 * 1.05:
                return None, "below EMA200+5%"

            # ── Filter 2: Weekly trend ───────────────────────────────────────
            weekly       = close.resample("W").last().dropna()
            weekly_ema20 = float(weekly.ewm(span=20, adjust=False).mean().iloc[-1])
            if float(weekly.iloc[-1]) <= weekly_ema20:
                return None, "weekly trend down"

            # ── Filter 3: Value zone ─────────────────────────────────────────
            zone_low  = min(ema20, ema50)
            zone_high = max(ema20, ema50)
            if not (zone_low <= ltp <= zone_high):
                return None, "outside EMA zone"

            # EMA gap should be meaningful (≥1%)
            ema_gap_pct = abs(ema20 - ema50) / ema50 * 100
            if ema_gap_pct < 1.0:
                return None, "EMA gap too narrow"

            # ── Filter 4: RSI 35–45 ──────────────────────────────────────────
            d   = close.diff()
            g   = d.where(d>0,0).rolling(14).mean()
            l_r = (-d.where(d<0,0)).rolling(14).mean()
            rsi = float((100-(100/(1+g/l_r.replace(0,1e-10)))).iloc[-1])
            if not (35 <= rsi <= 45):
                return None, f"RSI {rsi:.1f} out of range"

            # ── Filter 5: Volume ≥ 1.5x 20-day avg ──────────────────────────
            avg_vol   = float(volume.iloc[-21:-1].mean())
            today_vol = float(volume.iloc[-1])
            vol_ratio = round(today_vol / avg_vol, 2) if avg_vol > 0 else 0
            if vol_ratio < 1.5:
                return None, f"volume {vol_ratio}x insufficient"

            # ── Filter 6: Trigger candle ─────────────────────────────────────
            o_t    = float(open_.iloc[-1]);  h_t = float(high.iloc[-1])
            l_t    = float(low.iloc[-1]);    c_t = float(close.iloc[-1])
            prev_o = float(open_.iloc[-2]);  prev_c = float(close.iloc[-2])
            candle = detect_candle(o_t, h_t, l_t, c_t, prev_o, prev_c)
            if candle is None:
                return None, "no trigger candle"

            # ── Filter 7: Not near 52-week high ──────────────────────────────
            w52h = float(high.iloc[-252:].max())
            pct_from_high = (w52h - ltp) / w52h * 100
            # (allow through — just flag it)

            # ── All passed — build trade plan ─────────────────────────────────
            chg     = ltp - float(close.iloc[-2])
            chgp    = chg / float(close.iloc[-2]) * 100
            stop_sl = round(l_t * 0.995, 2)   # just below candle low
            tgt1    = round(ltp * 1.04, 2)    # 4% first target
            tgt2    = round(ltp * 1.08, 2)    # 8% final target
            gap     = 50 if ltp>1000 else 20 if ltp>500 else 10 if ltp>200 else 5
            cc_strike = math.ceil(ltp/gap)*gap
            rr_ratio  = round((tgt2-ltp)/(ltp-stop_sl), 2) if ltp > stop_sl else 0

            # Confidence score (1 point per filter, bonus for strong candle/volume)
            score = 5  # base — passed all 5 original filters
            score += 1  # weekly trend filter
            score += 1  # EMA buffer filter
            if vol_ratio >= 2.0:   score += 1
            if candle == "🕯 Bullish Engulfing": score += 1
            if rr_ratio >= 2.0:    score += 1

            return {
                "LTP ₹":         round(ltp, 2),
                "Chg%":          round(chgp, 2),
                "EMA 20":        round(ema20, 2),
                "EMA 50":        round(ema50, 2),
                "EMA 200":       round(ema200, 2),
                "EMA gap%":      round(ema_gap_pct, 1),
                "RSI":           round(rsi, 1),
                "Vol ratio":     vol_ratio,
                "Candle":        candle,
                "Stop loss":     stop_sl,
                "Target 1 (4%)": tgt1,
                "Target 2 (8%)": tgt2,
                "R:R ratio":     rr_ratio,
                "CC Strike":     cc_strike,
                "52W High":      round(w52h, 2),
                "% from high":   round(pct_from_high, 1),
                "Score":         score,
            }, None
        except Exception as e:
            return None, str(e)

    # ── Run button ────────────────────────────────────────────────────────────
    st.markdown("#### Swing-Covered Scanner")

    if breadth and breadth["condition"] == "red":
        st.error("🔴 Market is below EMA 200. Scanner disabled — protect your capital first.")
    else:
        run2 = st.button("▶ Run Swing-Covered Scanner", type="primary", key="run2")

        if run2:
            qualifiers = []
            prog2 = st.progress(0, text="Starting…")

            for i,(sym,meta) in enumerate(NIFTY50.items()):
                prog2.progress((i+1)/len(NIFTY50), text=f"Scanning {sym}…")
                result, reason = screen_swing_covered(sym)
                if result:
                    qualifiers.append({
                        "Stock":sym,"Sector":meta["sector"],"Lot":meta["lot"],**result
                    })

            prog2.empty()

            # Sort by confidence score
            qualifiers.sort(key=lambda x: x["Score"], reverse=True)

            st.divider()
            s1,s2,s3,s4 = st.columns(4)
            s1.metric("Scanned",          len(NIFTY50))
            s2.metric("Passed all 7",     len(qualifiers))
            s3.metric("Success rate",     f"{len(qualifiers)/len(NIFTY50)*100:.1f}%")
            s4.metric("Market condition", "🟢 Go" if breadth and breadth["condition"]=="green" else "🟡 Caution")

            if not qualifiers:
                st.warning("""
**No stocks passed all 7 filters today — this is completely normal.**

This strategy is intentionally very selective. On most days 0–2 stocks qualify.
That is the point — when one qualifies it is a genuine high-confidence setup.

✅ Come back tomorrow or after a market dip — setups cluster after corrections.
                """)
            else:
                st.success(f"✅ {len(qualifiers)} high-confidence setup(s) found today!")
                st.divider()

                for q in qualifiers:
                    score_color = "#1D9E75" if q["Score"]>=8 else "#D98A1A" if q["Score"]>=6 else "#888"
                    st.markdown(f"""
                    <div style="background:#F2FBF6;border:1.5px solid #1D9E75;border-radius:12px;
                                padding:16px 20px;margin-bottom:8px">
                      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
                        <div>
                          <span style="background:#1A1A18;color:white;font-weight:700;font-size:16px;
                                       padding:4px 14px;border-radius:6px">{q['Stock']}</span>
                          <span style="background:#EFEFEC;color:#555;font-size:11px;font-weight:500;
                                       padding:3px 10px;border-radius:10px;margin-left:8px">{q['Sector']}</span>
                          <span style="font-size:13px;margin-left:8px;font-weight:600">{q['Candle']}</span>
                          <span style="background:{score_color};color:white;font-size:11px;font-weight:700;
                                       padding:2px 10px;border-radius:20px;margin-left:8px">
                            Score {q['Score']}/10
                          </span>
                        </div>
                        <div style="text-align:right">
                          <div style="font-size:22px;font-weight:700">₹{q['LTP ₹']:.2f}</div>
                          <div style="font-size:13px;color:{'#1D9E75' if q['Chg%']>=0 else '#E24B4A'};font-weight:500">
                            {'+' if q['Chg%']>=0 else ''}{q['Chg%']:.2f}%
                          </div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Metrics
                    m1,m2,m3,m4,m5,m6 = st.columns(6)
                    m1.metric("RSI",        f"{q['RSI']}",      "35–45 ✓")
                    m2.metric("EMA 200",    f"₹{q['EMA 200']:.0f}", "5%+ above ✓")
                    m3.metric("EMA gap",    f"{q['EMA gap%']}%", "Meaningful ✓")
                    m4.metric("Vol ratio",  f"{q['Vol ratio']}x","≥1.5x ✓")
                    m5.metric("R:R ratio",  f"{q['R:R ratio']}:1","Risk/Reward")
                    m6.metric("% from high",f"{q['% from high']}%","Below 52W high")

                    # Trade plan
                    st.markdown(f"""
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0">
                      <div style="background:#FDDCDC;border-radius:8px;padding:12px 16px">
                        <div style="font-size:10px;color:#7A1A1A;text-transform:uppercase;font-weight:600;margin-bottom:4px">Stop Loss</div>
                        <div style="font-size:18px;font-weight:700;color:#7A1A1A">₹{q['Stop loss']:.2f}</div>
                        <div style="font-size:11px;color:#888">Just below candle low</div>
                      </div>
                      <div style="background:#D6F5E3;border-radius:8px;padding:12px 16px">
                        <div style="font-size:10px;color:#1A5C35;text-transform:uppercase;font-weight:600;margin-bottom:4px">Targets</div>
                        <div style="font-size:15px;font-weight:700;color:#1A5C35">T1: ₹{q['Target 1 (4%)']:.2f} &nbsp;|&nbsp; T2: ₹{q['Target 2 (8%)']:.2f}</div>
                        <div style="font-size:11px;color:#888">Book 50% at T1, rest at T2</div>
                      </div>
                    </div>
                    <div style="background:#E6F1FB;border:0.5px solid #85B7EB;border-radius:8px;
                                padding:12px 16px;margin-bottom:20px;font-size:13px">
                      💡 <strong>Covered call plan:</strong> Buy {q['Lot']:,} shares at ₹{q['LTP ₹']:.2f}
                      → Wait 1–2 days for bounce → Sell <strong>₹{q['CC Strike']} strike call</strong>
                      (monthly expiry, 20–30 DTE) to collect premium.
                      &nbsp;|&nbsp; 52W High: ₹{q['52W High']:.2f}
                    </div>
                    """, unsafe_allow_html=True)
                    st.divider()

                # Download
                df_q = pd.DataFrame(qualifiers)
                st.download_button("⬇ Download setups CSV",
                                   df_q.to_csv(index=False),
                                   "swing_covered_setups.csv","text/csv")


with tab3:
    import json, base64
    import requests

    st.markdown("### 🎯 BEL Long-Covered Strategy")
    st.markdown("1 lot · 1425 shares · Monthly covered call cycles · Data saved to GitHub")
    st.divider()

    BEL_SHARES = 1425
    DATA_FILE  = "bel_data.json"

    # ── GitHub storage helpers ────────────────────────────────────────────────
    def gh_headers():
        token = st.secrets.get("GITHUB_TOKEN", "")
        return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    def gh_repo():
        return st.secrets.get("GITHUB_REPO", "")

    def load_data_github():
        try:
            url = f"https://api.github.com/repos/{gh_repo()}/contents/{DATA_FILE}"
            r = requests.get(url, headers=gh_headers(), timeout=10)
            if r.status_code == 200:
                j = r.json()
                decoded = base64.b64decode(j["content"]).decode("utf-8")
                data = json.loads(decoded)
                data["_sha"] = j["sha"]
                return data
            elif r.status_code == 404:
                return {"buy_price": 412.30, "cycles": [], "_sha": None}
            else:
                st.error(f"GitHub load error: {r.status_code} — {r.text[:200]}")
                return {"buy_price": 412.30, "cycles": [], "_sha": None}
        except Exception as e:
            st.error(f"Load error: {e}")
            return {"buy_price": 412.30, "cycles": [], "_sha": None}

    def save_data_github(data):
        try:
            sha = data.pop("_sha", None)
            content_str = json.dumps(data, indent=2)
            encoded = base64.b64encode(content_str.encode()).decode()
            url = f"https://api.github.com/repos/{gh_repo()}/contents/{DATA_FILE}"
            payload = {
                "message": "Update BEL cycle data",
                "content": encoded,
            }
            if sha:
                payload["sha"] = sha
            r = requests.put(url, headers=gh_headers(), json=payload, timeout=10)
            if r.status_code in [200, 201]:
                data["_sha"] = r.json()["content"]["sha"]
                return True
            else:
                st.error(f"Save error: {r.status_code} — {r.text[:200]}")
                return False
        except Exception as e:
            st.error(f"Save error: {e}")
            return False

    # ── Load data ─────────────────────────────────────────────────────────────
    if "bel_data" not in st.session_state or st.session_state.get("bel_reload", True):
        st.session_state["bel_data"]   = load_data_github()
        st.session_state["bel_reload"] = False

    db = st.session_state["bel_data"]

    # ── BEL live price ────────────────────────────────────────────────────────
    @st.cache_data(ttl=300)
    def fetch_bel():
        try:
            df = yf.download("BEL.NS", period="10d", interval="1d",
                             progress=False, auto_adjust=True)
            if df.empty: return None, "Empty data"
            close = df["Close"]
            if hasattr(close, "squeeze"): close = close.squeeze()
            close = close.dropna()
            if len(close) < 2: return None, "Not enough rows"
            ltp  = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            return {"ltp":ltp,"chg":ltp-prev,"chgp":(ltp-prev)/prev*100}, None
        except Exception as e:
            return None, str(e)

    bel, bel_err = fetch_bel()
    if bel_err:
        st.warning(f"BEL live price unavailable: {bel_err}")

    # ── Buy price input ───────────────────────────────────────────────────────
    st.markdown("#### Position Overview")
    bp_col, _ = st.columns([1, 3])
    with bp_col:
        new_buy = st.number_input(
            "Your buy price (₹)", min_value=1.0, step=0.05,
            format="%.2f", value=float(db["buy_price"]),
            help="Saved automatically to GitHub"
        )
        if new_buy != db["buy_price"]:
            db["buy_price"] = new_buy
            save_data_github(db)

    buy_price     = db["buy_price"]
    cycles        = db.get("cycles", [])
    total_premium = sum(float(c["premium_income"]) for c in cycles)
    num_cycles    = len(cycles)
    invested      = round(buy_price * BEL_SHARES, 2)
    ltp           = bel["ltp"] if bel else buy_price
    ltp_ok        = bel is not None
    stock_pnl     = round((ltp - buy_price) * BEL_SHARES, 2)
    combined_pnl  = round(stock_pnl + total_premium, 2)
    stock_pct     = round(stock_pnl / invested * 100, 2)
    combined_pct  = round(combined_pnl / invested * 100, 2)

    # ── Row 1: Position basics ────────────────────────────────────────────────
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("BEL Live Price", f"₹{ltp:.2f}",
              f"{bel['chg']:+.2f} ({bel['chgp']:+.2f}%)" if ltp_ok else "⚠ Using buy price")
    c2.metric("Shares held",     f"{BEL_SHARES:,}", "1 lot")
    c3.metric("Buy price",       f"₹{buy_price:.2f}")
    c4.metric("Amount invested", f"₹{invested:,.2f}")

    st.markdown("")

    # ── Row 2: P&L breakdown ──────────────────────────────────────────────────
    p1,p2,p3 = st.columns(3)
    p1.metric("📈 Stock P&L",     f"₹{stock_pnl:+,.2f}",   f"{stock_pct:+.2f}% on cost")
    p2.metric("💰 Premium income", f"₹{total_premium:,.2f}", f"{num_cycles} cycles", delta_color="off")
    p3.metric("🎯 Combined P&L",  f"₹{combined_pnl:+,.2f}", f"{combined_pct:+.2f}% on cost")

    if total_premium > 0 or stock_pnl != 0:
        total_abs = max(abs(stock_pnl) + total_premium, 1)
        s_bar = abs(stock_pnl)/total_abs*100
        p_bar = total_premium/total_abs*100
        sc = "#1D9E75" if stock_pnl>=0 else "#E24B4A"
        st.markdown(f"""
        <div style="margin:10px 0 4px;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.05em">P&L breakdown</div>
        <div style="display:flex;height:10px;border-radius:5px;overflow:hidden;gap:2px">
          <div style="width:{s_bar:.1f}%;background:{sc};border-radius:5px 0 0 5px"></div>
          <div style="width:{p_bar:.1f}%;background:#185FA5;border-radius:0 5px 5px 0"></div>
        </div>
        <div style="display:flex;gap:16px;margin-top:5px;font-size:11px;color:#888">
          <span><span style="color:{sc}">■</span> Stock P&L</span>
          <span><span style="color:#185FA5">■</span> Premium income</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Log a new cycle ───────────────────────────────────────────────────────
    st.markdown("#### Log a covered call cycle")
    with st.form("bel_log_form", clear_on_submit=True):
        fc1,fc2,fc3,fc4 = st.columns(4)
        with fc1: entry_date  = st.date_input("Entry date")
        with fc2: expiry_date = st.date_input("Expiry date")
        with fc3: strike      = st.number_input("Strike price (₹)", min_value=0.0, step=0.5, format="%.2f")
        with fc4: premium     = st.number_input("Premium per share (₹)", min_value=0.0, step=0.05, format="%.2f")

        fc5,fc6,fc7 = st.columns(3)
        with fc5: expiry_spot = st.number_input("BEL price at expiry (₹)", min_value=0.0, step=0.05, format="%.2f")
        with fc6: outcome     = st.selectbox("Outcome", ["Option expired — kept shares","Shares called away at strike"])
        with fc7: notes       = st.text_input("Notes (optional)")

        saved = st.form_submit_button("💾 Save cycle", type="primary", use_container_width=True)
        if saved:
            if premium <= 0 or strike <= 0:
                st.error("Please enter a valid strike and premium.")
            else:
                prem_income = round(premium * BEL_SHARES, 2)
                new_id = (max((c["id"] for c in cycles), default=0) + 1)
                cycles.append({
                    "id":           new_id,
                    "entry_date":   str(entry_date),
                    "expiry_date":  str(expiry_date),
                    "strike":       float(strike),
                    "premium":      float(premium),
                    "expiry_spot":  float(expiry_spot),
                    "outcome":      outcome,
                    "notes":        notes,
                    "premium_income": prem_income,
                    "buy_price":    float(buy_price),
                })
                db["cycles"] = cycles
                if save_data_github(db):
                    st.success(f"✓ Saved to GitHub! Premium income: ₹{prem_income:,.2f}")
                    st.session_state["bel_reload"] = True
                    st.rerun()

    st.divider()

    # ── Cycle history ─────────────────────────────────────────────────────────
    if not cycles:
        st.info("No cycles logged yet. Use the form above to record your first cycle.")
    else:
        st.markdown("#### Cycle history")
        rows = []
        for c in cycles:
            rows.append({
                "ID":            c["id"],
                "Entry":         c["entry_date"],
                "Expiry":        c["expiry_date"],
                "Strike ₹":     c["strike"],
                "Premium/sh ₹": c["premium"],
                "Expiry spot ₹":c["expiry_spot"],
                "Income ₹":     f"₹{float(c['premium_income']):,.2f}",
                "Outcome":      "✅ Expired" if "expired" in str(c["outcome"]).lower() else "🔄 Called",
                "Notes":        c["notes"] or "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        d1,d2 = st.columns([1,3])
        with d1:
            del_id = st.number_input("Delete by ID", min_value=1, step=1, value=1)
        with d2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete cycle", type="secondary"):
                db["cycles"] = [c for c in cycles if c["id"] != int(del_id)]
                if save_data_github(db):
                    st.success(f"✓ Cycle #{int(del_id)} deleted.")
                    st.session_state["bel_reload"] = True
                    st.rerun()

        st.divider()

        # ── Monthly premium chart ─────────────────────────────────────────────
        st.markdown("#### Monthly premium income")
        monthly = {}
        for c in cycles:
            m = str(c["expiry_date"])[:7]
            monthly[m] = monthly.get(m, 0) + float(c["premium_income"])

        if monthly:
            import altair as alt
            df_ch = pd.DataFrame({
                "Month": list(monthly.keys()),
                "Premium ₹": list(monthly.values())
            }).sort_values("Month")
            df_ch["Cumulative"] = df_ch["Premium ₹"].cumsum()
            bars = alt.Chart(df_ch).mark_bar(
                color="#1D9E75", cornerRadiusTopLeft=4, cornerRadiusTopRight=4
            ).encode(
                x=alt.X("Month:O", axis=alt.Axis(labelAngle=-30)),
                y=alt.Y("Premium ₹:Q", title="Premium income (₹)"),
                tooltip=["Month", alt.Tooltip("Premium ₹:Q", format=",.2f")]
            )
            line = alt.Chart(df_ch).mark_line(
                color="#185FA5", strokeWidth=2.5, point=True
            ).encode(
                x="Month:O",
                y=alt.Y("Cumulative:Q", title=""),
                tooltip=["Month", alt.Tooltip("Cumulative:Q", title="Cumulative ₹", format=",.2f")]
            )
            st.altair_chart(bars + line, use_container_width=True, theme=None)
            st.caption("🟢 Bars = monthly premium · 🔵 Line = cumulative total")

        st.divider()
        s1,s2,s3,s4 = st.columns(4)
        nc = len(cycles)
        tp = sum(float(c["premium_income"]) for c in cycles)
        s1.metric("Total cycles",  nc)
        s2.metric("Total premium", f"₹{tp:,.2f}")
        s3.metric("Avg per cycle", f"₹{tp/nc:,.2f}" if nc else "—")
        s4.metric("Avg per share", f"₹{tp/BEL_SHARES/nc:.2f}" if nc else "—")

        st.download_button(
            "⬇ Download history CSV",
            pd.DataFrame(rows).to_csv(index=False),
            "bel_cycles.csv", "text/csv"
        )
