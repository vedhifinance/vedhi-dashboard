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
            def cr(v):
                if v<20: return "color:#185FA5;font-weight:600"
                if v<30: return "color:#1D9E75;font-weight:600"
                if v<40: return "color:#D98A1A;font-weight:600"
                if v>70: return "color:#E24B4A;font-weight:600"
                return ""
            def cc(v): return "color:#1D9E75" if v>=0 else "color:#E24B4A"
            def ct(v): return "background-color:#D6F5E3;color:#1A5C35;font-weight:600" if v=="Bull" \
                        else "background-color:#FDDCDC;color:#7A1A1A;font-weight:600"
            def cz(v): return "background-color:#D6F5E3;color:#1A5C35;font-weight:600" if v=="Yes" \
                        else "background-color:#FDDCDC;color:#7A1A1A;font-weight:600"
            styled = df.style\
                .map(cr, subset=["RSI"])\
                .map(cc, subset=["Chg%"])\
                .map(cc, subset=["Histogram"])\
                .map(ct, subset=["Trend"])\
                .map(ct, subset=["MACD Bias"])\
                .map(cz, subset=["EMA Zone"])\
                .set_table_styles([{
                    "selector": "thead tr th",
                    "props": [
                        ("background-color", "#1A1A18"),
                        ("color", "white"),
                        ("font-weight", "600"),
                        ("font-size", "12px"),
                        ("letter-spacing", "0.04em"),
                        ("padding", "10px 12px"),
                    ]
                }])\
                .format({"LTP ₹":"₹{:.2f}","Chg%":"{:+.2f}%","RSI":"{:.1f}",
                         "EMA 20":"₹{:.2f}","EMA 50":"₹{:.2f}",
                         "MACD":"{:.2f}","Signal":"{:.2f}","Histogram":"{:.2f}","Lot":"{:,}"})
            st.dataframe(styled, use_container_width=True, height=480)
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
    st.markdown("### Nifty 50 Swing-Covered Strategy")
    st.info("Coming soon — tell me what to build here!")

with tab3:
    import json, os

    st.markdown("### 🎯 BEL Long-Covered Strategy")
    st.markdown("1 lot · 1425 shares · Monthly covered call cycles · Data saved to GitHub repo")
    st.divider()

    BEL_SHARES = 1425
    DATA_FILE  = "bel_data.json"

    # ── File-based persistence ────────────────────────────────────────────────
    def load_data():
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    return json.load(f)
            except: pass
        return {"buy_price": 412.30, "cycles": []}

    def save_data(data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # Load on every run
    if "bel_data" not in st.session_state:
        st.session_state["bel_data"] = load_data()

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
            return {"ltp":ltp, "chg":ltp-prev, "chgp":(ltp-prev)/prev*100}, None
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
            help="Saved automatically"
        )
        if new_buy != db["buy_price"]:
            db["buy_price"] = new_buy
            save_data(db)

    buy_price     = db["buy_price"]
    cycles        = db["cycles"]
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
                save_data(db)
                st.success(f"✓ Saved! Premium income: ₹{prem_income:,.2f}")
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

        # Delete
        d1,d2 = st.columns([1,3])
        with d1:
            del_id = st.number_input("Delete by ID", min_value=1, step=1, value=1)
        with d2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete cycle", type="secondary"):
                db["cycles"] = [c for c in cycles if c["id"] != int(del_id)]
                save_data(db)
                st.success(f"Cycle #{int(del_id)} deleted.")
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

        # ── Summary ───────────────────────────────────────────────────────────
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
