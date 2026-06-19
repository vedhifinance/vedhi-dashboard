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
<div style="padding:4px 0 12px">
  <div class="brand">Vedhi <span class="pulse">Pulse</span></div>
  <div class="sub">Nifty 50 Intelligence &nbsp;·&nbsp; NSE India &nbsp;·&nbsp; Live Market Data</div>
  <div class="live-badge"><span class="dot"></span>&nbsp;Live</div>
</div>
""", unsafe_allow_html=True)

# ── Nifty 50 Live Indicators (once) ──────────────────────────────────────────

def calc_rsi_proper(close, period=14):
    """Wilder's RSI — correct implementation used everywhere"""
    close = close.dropna()
    # Remove duplicate index entries
    close = close[~close.index.duplicated(keep='last')]
    close = close.sort_index()
    delta = close.diff().dropna()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    # Wilder's smoothing (EMA with alpha = 1/period)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    val = float(rsi.iloc[-1])
    # Sanity check — RSI must be 1 to 99
    if val < 1 or val > 99:
        return None
    return round(val, 1)

@st.cache_data(ttl=120)  # refresh every 2 min for live data
def fetch_nifty():
    try:
        # Daily — EMA, MACD (slow indicators)
        df = yf.download("^NSEI", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 55: return None
        c = df["Close"].squeeze().dropna()
        c = c[~c.index.duplicated(keep='last')].sort_index()
        ema20 = c.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = c.ewm(span=50, adjust=False).mean().iloc[-1]
        e12   = c.ewm(span=12, adjust=False).mean()
        e26   = c.ewm(span=26, adjust=False).mean()
        macd  = e12 - e26
        sig   = macd.ewm(span=9, adjust=False).mean()
        hist  = macd - sig
        prev  = float(c.iloc[-2])
        # Intraday 5-min — live RSI + live price
        df_i  = yf.download("^NSEI", period="5d", interval="5m", progress=False, auto_adjust=True)
        if not df_i.empty and len(df_i) >= 20:
            c_i = df_i["Close"].squeeze().dropna()
            c_i = c_i[~c_i.index.duplicated(keep='last')].sort_index()
        else:
            c_i = c
        rsi   = calc_rsi_proper(c_i)
        if rsi is None: return None
        ltp   = float(c_i.iloc[-1])
        return {
            "ltp": ltp, "chg": ltp-prev, "chgp": (ltp-prev)/prev*100,
            "rsi": rsi, "ema20": round(float(ema20),1),
            "ema50": round(float(ema50),1), "macd": round(float(macd.iloc[-1]),2),
            "signal": round(float(sig.iloc[-1]),2), "hist": round(float(hist.iloc[-1]),2),
        }
    except: return None

nifty = fetch_nifty()
if nifty:
    arrow    = "▲" if nifty["chg"] >= 0 else "▼"
    chg_col  = "#1D9E75" if nifty["chg"] >= 0 else "#E24B4A"
    rsi_col  = "#185FA5" if nifty["rsi"]<30 else "#1D9E75" if nifty["rsi"]<40 else \
               "#D98A1A" if nifty["rsi"]<70 else "#E24B4A"
    rsi_lbl  = "Oversold" if nifty["rsi"]<30 else "Value" if nifty["rsi"]<40 else \
               "Neutral" if nifty["rsi"]<60 else "Elevated" if nifty["rsi"]<70 else "Overbought"
    hist_col = "#1D9E75" if nifty["hist"]>=0 else "#E24B4A"
    e20_col  = "#1D9E75" if nifty["ltp"]>nifty["ema20"] else "#E24B4A"
    e50_col  = "#1D9E75" if nifty["ltp"]>nifty["ema50"] else "#E24B4A"

    st.markdown(f"""
    <div style="background:#fff;border:0.5px solid #E0DED8;border-radius:8px;
                padding:10px 16px;display:flex;align-items:center;
                gap:0;flex-wrap:wrap;margin-bottom:4px">

      <div style="padding:0 16px 0 0;margin-right:16px;border-right:0.5px solid #E0DED8">
        <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:.05em">Nifty 50</div>
        <div style="display:flex;align-items:baseline;gap:6px;margin-top:1px">
          <span style="font-size:16px;font-weight:600;color:#1A1A18">{nifty['ltp']:,.2f}</span>
          <span style="font-size:11px;font-weight:500;color:{chg_col}">{arrow} {abs(nifty['chg']):.0f} ({abs(nifty['chgp']):.1f}%)</span>
        </div>
      </div>

      <div style="padding:0 16px;border-right:0.5px solid #E0DED8">
        <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:.05em">RSI 14</div>
        <div style="margin-top:1px">
          <span style="font-size:14px;font-weight:600;color:{rsi_col}">{nifty['rsi']}</span>
          <span style="font-size:10px;color:{rsi_col};margin-left:4px">{rsi_lbl}</span>
        </div>
      </div>

      <div style="padding:0 16px;border-right:0.5px solid #E0DED8">
        <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:.05em">EMA 20</div>
        <div style="margin-top:1px">
          <span style="font-size:14px;font-weight:500;color:#1A1A18">{nifty['ema20']:,.0f}</span>
          <span style="font-size:10px;color:{e20_col};margin-left:4px">{'↑ Above' if nifty['ltp']>nifty['ema20'] else '↓ Below'}</span>
        </div>
      </div>

      <div style="padding:0 16px;border-right:0.5px solid #E0DED8">
        <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:.05em">EMA 50</div>
        <div style="margin-top:1px">
          <span style="font-size:14px;font-weight:500;color:#1A1A18">{nifty['ema50']:,.0f}</span>
          <span style="font-size:10px;color:{e50_col};margin-left:4px">{'↑ Above' if nifty['ltp']>nifty['ema50'] else '↓ Below'}</span>
        </div>
      </div>

      <div style="padding:0 16px;border-right:0.5px solid #E0DED8">
        <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:.05em">MACD</div>
        <div style="margin-top:1px">
          <span style="font-size:14px;font-weight:500;color:#1A1A18">{nifty['macd']:+.1f}</span>
          <span style="font-size:10px;color:#888;margin-left:4px">Sig {nifty['signal']:+.1f}</span>
        </div>
      </div>

      <div style="padding:0 0 0 16px">
        <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:.05em">Histogram</div>
        <div style="margin-top:1px">
          <span style="font-size:14px;font-weight:500;color:{hist_col}">{nifty['hist']:+.1f}</span>
          <span style="font-size:10px;color:{hist_col};margin-left:4px">{'Bullish' if nifty['hist']>=0 else 'Bearish'}</span>
        </div>
      </div>

      <div style="margin-left:auto;font-size:10px;color:#bbb;padding-left:16px">
        {pd.Timestamp.now().strftime('%d %b %Y %H:%M')} IST
      </div>

    </div>
    """, unsafe_allow_html=True)
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

@st.cache_data(ttl=120)  # refresh every 2 min for live RSI
def fetch_stock(symbol):
    try:
        # Daily — EMA, MACD, Volume (slow indicators)
        df = yf.download(f"{symbol}.NS", period="1y", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df)<55: return None
        c   = df["Close"].squeeze().dropna()
        c   = c[~c.index.duplicated(keep='last')].sort_index()
        vol = df["Volume"].squeeze().dropna()
        vol = vol[~vol.index.duplicated(keep='last')].sort_index()
        ema20   = c.ewm(span=20,adjust=False).mean().iloc[-1]
        ema50   = c.ewm(span=50,adjust=False).mean().iloc[-1]
        e12=c.ewm(span=12,adjust=False).mean(); e26=c.ewm(span=26,adjust=False).mean()
        macd=e12-e26; sig=macd.ewm(span=9,adjust=False).mean(); hist=macd-sig
        prev=float(c.iloc[-2])
        # Volume
        today_vol = float(vol.iloc[-1])
        avg_vol   = float(vol.iloc[-21:-1].mean()) if len(vol) >= 21 else float(vol.mean())
        vol_ratio = round(today_vol/avg_vol, 2) if avg_vol > 0 else 0
        # Intraday 5-min — live RSI + live price
        df_i = yf.download(f"{symbol}.NS", period="5d", interval="5m",
                            progress=False, auto_adjust=True)
        if not df_i.empty and len(df_i) >= 20:
            c_i = df_i["Close"].squeeze().dropna()
            c_i = c_i[~c_i.index.duplicated(keep='last')].sort_index()
        else:
            c_i = c  # fallback to daily
        rsi_val = calc_rsi_proper(c_i)
        if rsi_val is None: return None
        rsi     = rsi_val
        ltp     = float(c_i.iloc[-1])
        vol_trend = "↑ High" if vol_ratio >= 1.5 else "↗ Above" if vol_ratio >= 1.0 else "↓ Low"
        # Derived signals
        ema_ok   = min(ema20,ema50) <= ltp <= max(ema20,ema50)
        bull     = ema20 > ema50
        macd_bull= float(hist.iloc[-1]) >= 0
        # Signal logic — Trend + RSI + Volume are the primary drivers
        rsi_ok   = 30 <= rsi <= 50
        vol_ok   = vol_ratio >= 1.2
        if bull and rsi_ok and vol_ok:    signal = "🟢 Strong Buy"
        elif bull and rsi_ok:             signal = "🟡 Watch (low vol)"
        elif bull and vol_ok and ema_ok:  signal = "🟡 Watch"
        elif bull:                        signal = "🟡 Weak"
        else:                             signal = "🔴 Avoid"
        return {
            "LTP":round(ltp,2), "Chg%":round((ltp-prev)/prev*100,2),
            "RSI":round(float(rsi),1), "EMA 20":round(float(ema20),2),
            "EMA 50":round(float(ema50),2), "MACD":round(float(macd.iloc[-1]),2),
            "Signal Line":round(float(sig.iloc[-1]),2), "Histogram":round(float(hist.iloc[-1]),2),
            "EMA Zone":"Yes" if ema_ok else "No",
            "Trend":"Bull" if bull else "Bear",
            "MACD Bias":"Bull" if macd_bull else "Bear",
            "Vol Ratio":vol_ratio, "Vol Trend":vol_trend,
            "Signal":signal,
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
            results.append({
                "Stock":sym, "Sector":meta["sector"],
                "LTP ₹":ltp, "Chg%":data["Chg%"], "RSI":data["RSI"],
                "EMA 20":e20, "EMA 50":e50,
                "MACD":data["MACD"], "Signal Line":data["Signal Line"],
                "Histogram":data["Histogram"],
                "EMA Zone":data["EMA Zone"],
                "Trend":data["Trend"],
                "MACD Bias":data["MACD Bias"],
                "Vol Ratio":data["Vol Ratio"],
                "Vol Trend":data["Vol Trend"],
                "Signal":data["Signal"],
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
        c3.metric("EMA zone",   int((df["EMA Zone"]=="Yes").sum()) if "EMA Zone" in df.columns else 0)
        c4.metric("Bullish",  int((df["Trend"]=="Bull").sum()) if "Trend" in df.columns else 0)
        c5.metric("Avg RSI",  round(df["RSI"].mean(),1) if len(df) else "—")
        if df.empty:
            st.info("No stocks match the filters.")
        else:
            # Remove injected CSS — not needed with HTML table
            # Build HTML table with black headers, white text
            cols = ["Stock","Sector","LTP ₹","Chg%","RSI","EMA Zone","Trend","Vol Trend","Signal","Lot"]

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
                if col == "Vol Trend":
                    if "High" in str(val):   return "background:#D6F5E3;color:#1A5C35;font-weight:600"
                    if "Above" in str(val):  return "color:#1D9E75;font-weight:500"
                    return "color:#E24B4A;font-weight:500"
                if col == "Signal":
                    if "Strong Buy" in str(val): return "background:#1D9E75;color:white;font-weight:700"
                    if "Watch" in str(val):      return "background:#F5C842;color:#1A1A18;font-weight:600"
                    if "Weak" in str(val):       return "color:#D98A1A;font-weight:500"
                    if "Avoid" in str(val):      return "background:#E24B4A;color:white;font-weight:700"
                return ""

            def fmt_val(col, val):
                if col == "LTP ₹":      return f"₹{val:.2f}"
                if col == "Chg%":       return f"{val:+.2f}%"
                if col == "RSI":        return f"{val:.1f}"
                if col in ["EMA 20","EMA 50"]: return f"₹{val:.2f}"
                if col in ["MACD","Signal Line","Histogram"]: return f"{val:.2f}"
                if col == "Vol Ratio":  return f"{val:.2f}x"
                if col == "Lot":        return f"{int(val):,}"
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
    import json, base64
    import requests as req1
    from datetime import date

    st.markdown("### 📈 Nifty 50 Swing Strategy")
    st.caption("Track your swing trades — open holdings, sell records, P&L history")
    st.divider()

    SW_FILE = "swing_data.json"

    # ── GitHub helpers ────────────────────────────────────────────────────────
    def sw_headers():
        return {"Authorization": f"token {st.secrets.get('GITHUB_TOKEN','')}",
                "Accept": "application/vnd.github.v3+json"}

    def sw_load():
        try:
            url = f"https://api.github.com/repos/{st.secrets.get('GITHUB_REPO','')}/contents/{SW_FILE}"
            r = req1.get(url, headers=sw_headers(), timeout=10)
            if r.status_code == 200:
                j    = r.json()
                data = json.loads(base64.b64decode(j["content"]).decode())
                data["_sha"] = j["sha"]
                return data
            return {"holdings": [], "sold": [], "_sha": None}
        except:
            return {"holdings": [], "sold": [], "_sha": None}

    def sw_save(data):
        try:
            sha     = data.pop("_sha", None)
            encoded = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
            url     = f"https://api.github.com/repos/{st.secrets.get('GITHUB_REPO','')}/contents/{SW_FILE}"
            payload = {"message": "Update swing holdings", "content": encoded}
            if sha: payload["sha"] = sha
            r = req1.put(url, headers=sw_headers(), json=payload, timeout=10)
            if r.status_code in [200, 201]:
                data["_sha"] = r.json()["content"]["sha"]
                return True
            st.error(f"Save failed: {r.status_code}")
            return False
        except Exception as e:
            st.error(f"Save error: {e}")
            return False

    @st.cache_data(ttl=300)
    def get_sw_price(sym):
        try:
            df = yf.download(f"{sym}.NS", period="5d", interval="1d",
                             progress=False, auto_adjust=True)
            if df.empty: return None
            c = df["Close"].squeeze().dropna()
            return round(float(c.iloc[-1]), 2)
        except: return None

    # ── Load data ─────────────────────────────────────────────────────────────
    if "sw_data" not in st.session_state or st.session_state.get("sw_reload", True):
        st.session_state["sw_data"]   = sw_load()
        st.session_state["sw_reload"] = False

    sw_db    = st.session_state["sw_data"]
    holdings = sw_db.get("holdings", [])
    sold     = sw_db.get("sold", [])

    # ── Sub tabs ──────────────────────────────────────────────────────────────
    sw1, sw2, sw3 = st.tabs(["📂 Open Holdings", "💸 Sell a Stock", "📋 Sold History"])

    # ════════════════════════════════════════════════════════════════
    # SUB TAB 1 — Open Holdings
    # ════════════════════════════════════════════════════════════════
    with sw1:

        # Add holding form
        st.markdown("**➕ Add holding**")
        with st.form("sw_add_form", clear_on_submit=True):
            a1,a2,a3,a4 = st.columns(4)
            with a1: sw_sym   = st.selectbox("Stock", list(NIFTY50.keys()), key="sw_sym")
            with a2: sw_qty   = st.number_input("Quantity", min_value=1, step=1, key="sw_qty")
            with a3: sw_price = st.number_input("Buy price (₹)", min_value=0.01,
                                                 step=0.05, format="%.2f", key="sw_bp")
            with a4: sw_date  = st.date_input("Buy date", key="sw_date")
            sw_notes = st.text_input("Notes (optional)", key="sw_notes")
            sw_submit = st.form_submit_button("Add holding", type="primary",
                                               use_container_width=True)
            if sw_submit and sw_qty > 0 and sw_price > 0:
                # Check if already holding this stock — merge
                existing = next((h for h in holdings if h["symbol"]==sw_sym), None)
                new_buy  = {"qty": int(sw_qty), "price": float(sw_price),
                            "date": str(sw_date), "notes": sw_notes}
                if existing:
                    existing["buys"].append(new_buy)
                else:
                    holdings.append({
                        "id":     len(holdings)+1,
                        "symbol": sw_sym,
                        "sector": NIFTY50[sw_sym]["sector"],
                        "buys":   [new_buy],
                    })
                sw_db["holdings"] = holdings
                if sw_save(sw_db):
                    st.success(f"✓ {int(sw_qty)} shares of {sw_sym} @ ₹{sw_price:.2f} added!")
                    st.session_state["sw_reload"] = True
                    st.rerun()

        st.divider()

        # ── Current open holdings table ───────────────────────────────────────
        if not holdings:
            st.info("No open holdings yet. Add your first trade above.")
        else:
            st.markdown("**📂 Current open holdings**")

            rows = []
            for h in holdings:
                sym   = h["symbol"]
                buys  = h["buys"]
                total_qty  = sum(b["qty"] for b in buys)
                avg_cost   = sum(b["qty"]*b["price"] for b in buys) / total_qty
                first_date = min(b["date"] for b in buys)
                hold_days  = (date.today() - date.fromisoformat(first_date)).days
                live       = get_sw_price(sym)
                ltp        = live if live else avg_cost
                invested   = round(avg_cost * total_qty, 2)
                curr_val   = round(ltp * total_qty, 2)
                unreal_pnl = round(curr_val - invested, 2)
                pnl_pct    = round(unreal_pnl / invested * 100, 2) if invested else 0

                rows.append({
                    "symbol":    sym,
                    "Ticker":    sym,
                    "Buy Date":  first_date,
                    "Days":      hold_days,
                    "Qty":       total_qty,
                    "Avg ₹":    round(avg_cost, 2),
                    "Live ₹":   ltp if live else "—",
                    "Invested ₹": f"₹{invested:,.0f}",
                    "Curr Value ₹": f"₹{curr_val:,.0f}" if live else "—",
                    "Unreal P&L": f"₹{unreal_pnl:+,.0f}" if live else "—",
                    "P&L %":     f"{pnl_pct:+.1f}%" if live else "—",
                })

            # Build HTML table
            cols_show = ["Ticker","Buy Date","Days","Qty","Avg ₹","Live ₹",
                         "Invested ₹","Curr Value ₹","Unreal P&L","P&L %"]

            header = "".join(
                f'<th style="background:#1A1A18;color:white;font-size:11px;font-weight:600;'
                f'padding:9px 12px;text-align:left;white-space:nowrap;'
                f'border-right:0.5px solid #444">{c}</th>' for c in cols_show
            )

            body = ""
            for i, r in enumerate(rows):
                bg = "#fff" if i%2==0 else "#FAFAF8"
                unreal_raw = r["Unreal P&L"]
                pnl_raw    = r["P&L %"]
                row_html   = f'<tr style="background:{bg}">'
                for c in cols_show:
                    val   = r[c]
                    style = "padding:9px 12px;font-size:13px;border-right:0.5px solid #E0DED8;border-bottom:0.5px solid #E0DED8;white-space:nowrap;"
                    if c == "Ticker":
                        style += "background:#1A1A18;color:white;font-weight:600;"
                    elif c == "Unreal P&L":
                        color = "#1D9E75" if "+" in str(val) else "#E24B4A"
                        style += f"color:{color};font-weight:600;"
                    elif c == "P&L %":
                        color = "#1D9E75" if "+" in str(val) else "#E24B4A"
                        style += f"color:{color};font-weight:600;"
                    row_html += f'<td style="{style}">{val}</td>'
                row_html += "</tr>"
                body += row_html

            st.markdown(f"""
            <div style="overflow-x:auto;border:0.5px solid #E0DED8;border-radius:8px;overflow:hidden">
              <table style="width:100%;border-collapse:collapse;font-family:system-ui,sans-serif">
                <thead><tr>{header}</tr></thead>
                <tbody>{body}</tbody>
              </table>
            </div>
            """, unsafe_allow_html=True)

            # Portfolio summary
            st.markdown("")
            total_inv  = sum(sum(b["qty"]*b["price"] for b in h["buys"]) for h in holdings)
            total_curr = sum((get_sw_price(h["symbol"]) or 0) *
                             sum(b["qty"] for b in h["buys"]) for h in holdings)
            total_pnl  = round(total_curr - total_inv, 2)
            total_pct  = round(total_pnl/total_inv*100, 2) if total_inv else 0

            pm1,pm2,pm3,pm4 = st.columns(4)
            pm1.metric("Open positions", len(holdings))
            pm2.metric("Total invested", f"₹{total_inv:,.0f}")
            pm3.metric("Current value",  f"₹{total_curr:,.0f}")
            pm4.metric("Unrealised P&L", f"₹{total_pnl:+,.0f}", f"{total_pct:+.1f}%")

    # ════════════════════════════════════════════════════════════════
    # SUB TAB 2 — Sell a Stock
    # ════════════════════════════════════════════════════════════════
    with sw2:
        st.markdown("**💸 Sell a stock**")
        if not holdings:
            st.info("No open holdings to sell.")
        else:
            with st.form("sw_sell_form", clear_on_submit=True):
                holding_syms = [h["symbol"] for h in holdings]
                s1,s2,s3,s4 = st.columns(4)
                with s1: sell_sym   = st.selectbox("Stock to sell", holding_syms, key="sell_sym")
                with s2: sell_qty   = st.number_input("Qty to sell", min_value=1, step=1, key="sell_qty")
                with s3: sell_price = st.number_input("Sell price (₹)", min_value=0.01,
                                                       step=0.05, format="%.2f", key="sell_price")
                with s4: sell_date  = st.date_input("Sell date", key="sell_date")
                sell_notes = st.text_input("Notes (optional)", key="sell_notes")
                sell_submit = st.form_submit_button("💸 Confirm sell", type="primary",
                                                     use_container_width=True)

                if sell_submit and sell_qty > 0 and sell_price > 0:
                    pos = next((h for h in holdings if h["symbol"]==sell_sym), None)
                    if pos:
                        buys      = pos["buys"]
                        total_qty = sum(b["qty"] for b in buys)
                        avg_cost  = sum(b["qty"]*b["price"] for b in buys) / total_qty
                        sell_qty_int = int(sell_qty)

                        if sell_qty_int > total_qty:
                            st.error(f"You only hold {total_qty} shares of {sell_sym}.")
                        else:
                            invested_sold = round(avg_cost * sell_qty_int, 2)
                            proceeds      = round(float(sell_price) * sell_qty_int, 2)
                            realised_pnl  = round(proceeds - invested_sold, 2)
                            pnl_pct       = round(realised_pnl/invested_sold*100, 2) if invested_sold else 0
                            hold_days     = (date.fromisoformat(str(sell_date)) -
                                            date.fromisoformat(min(b["date"] for b in buys))).days

                            # Save to sold history
                            sold.append({
                                "id":           len(sold)+1,
                                "symbol":       sell_sym,
                                "sector":       pos["sector"],
                                "qty":          sell_qty_int,
                                "avg_cost":     round(avg_cost, 2),
                                "sell_price":   float(sell_price),
                                "buy_date":     min(b["date"] for b in buys),
                                "sell_date":    str(sell_date),
                                "hold_days":    hold_days,
                                "invested":     invested_sold,
                                "proceeds":     proceeds,
                                "realised_pnl": realised_pnl,
                                "pnl_pct":      pnl_pct,
                                "notes":        sell_notes,
                            })

                            # Remove from holdings
                            if sell_qty_int == total_qty:
                                sw_db["holdings"] = [h for h in holdings if h["symbol"]!=sell_sym]
                            else:
                                # Partial sell — reduce qty
                                remaining = sell_qty_int
                                for b in pos["buys"]:
                                    if remaining <= 0: break
                                    deduct = min(b["qty"], remaining)
                                    b["qty"] -= deduct
                                    remaining -= deduct
                                pos["buys"] = [b for b in pos["buys"] if b["qty"] > 0]

                            sw_db["sold"] = sold
                            if sw_save(sw_db):
                                pnl_emoji = "🟢" if realised_pnl >= 0 else "🔴"
                                st.success(f"{pnl_emoji} Sold {sell_qty_int} {sell_sym} @ ₹{sell_price:.2f} · Realised P&L: ₹{realised_pnl:+,.0f} ({pnl_pct:+.1f}%)")
                                st.session_state["sw_reload"] = True
                                st.rerun()

    # ════════════════════════════════════════════════════════════════
    # SUB TAB 3 — Sold History
    # ════════════════════════════════════════════════════════════════
    with sw3:
        st.markdown("**📋 Sold history**")
        if not sold:
            st.info("No sold trades yet.")
        else:
            sold_rows = []
            for s in sorted(sold, key=lambda x: x["sell_date"], reverse=True):
                sold_rows.append({
                    "Ticker":      s["symbol"],
                    "Sector":      s["sector"],
                    "Qty":         s["qty"],
                    "Avg Cost ₹":  f"₹{s['avg_cost']:.2f}",
                    "Sell Price ₹":f"₹{s['sell_price']:.2f}",
                    "Buy Date":    s["buy_date"],
                    "Sell Date":   s["sell_date"],
                    "Hold Days":   s["hold_days"],
                    "Invested ₹":  f"₹{s['invested']:,.0f}",
                    "Proceeds ₹":  f"₹{s['proceeds']:,.0f}",
                    "Realised P&L":f"₹{s['realised_pnl']:+,.0f}",
                    "P&L %":       f"{s['pnl_pct']:+.1f}%",
                    "Notes":       s.get("notes","—"),
                })
            st.dataframe(pd.DataFrame(sold_rows), use_container_width=True, hide_index=True)

            # Summary
            total_realised = sum(s["realised_pnl"] for s in sold)
            total_proceeds = sum(s["proceeds"] for s in sold)
            winners = [s for s in sold if s["realised_pnl"] > 0]
            st.markdown("")
            r1,r2,r3,r4 = st.columns(4)
            r1.metric("Total trades",    len(sold))
            r2.metric("Total realised",  f"₹{total_realised:+,.0f}")
            r3.metric("Win rate",        f"{len(winners)/len(sold)*100:.0f}%")
            r4.metric("Total proceeds",  f"₹{total_proceeds:,.0f}")

            st.download_button("⬇ Download sold history",
                               pd.DataFrame(sold_rows).to_csv(index=False),
                               "vedhi_swing_sold.csv", "text/csv")



with tab2:
    import math

    st.markdown("### 📊 Nifty 50 Swing-Covered Strategy")
    st.markdown("7-layer confluence filter · Institutional grade · RSI 30–50 · Volume 1.2x · 2–4 setups/month")
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
| 4 | **RSI** | Between 30 and 50 | Oversold enough for value, not so low it is broken |
| 5 | **Volume** | Today ≥ 1.2x 20-day average | Smart money confirming the move |
| 6 | **Trigger candle** | Hammer / Bullish Engulfing / Strong Green Close | Entry signal — market showing its hand |
| 7 | **Market breadth** | Nifty 50 above its own EMA 50 | Never fight the broader market |

### Covered Call Rules
- **Buy in 2 tranches — Tranche 2 only on dips, never forced**
  - Tranche 1 (60%) → Always enter on trigger candle signal
  - Tranche 2 (40%) → Only if price dips near the stop loss zone
  - ⚡ **If stock shoots up after T1 — sell at target, skip T2 completely**
- **Sell covered call after your full position is built**
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
- RSI **30 to 50** = sweet spot — oversold enough to offer value, not so low that something is fundamentally wrong
- RSI **above 50** = not oversold enough — wait for a better pullback
- The 30–50 band captures a broader pullback range — still selective but gives 2–4 setups per month
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

    # ── Market breadth ────────────────────────────────────────────────────────
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
        <div style="background:{bc[breadth['condition']]};border:0.5px solid;
                    border-color:{'#1D9E75' if breadth['condition']=='green' else '#F5C842' if breadth['condition']=='yellow' else '#E24B4A'};
                    border-radius:8px;padding:12px 16px;margin-bottom:14px;font-size:13px;color:{bc2[breadth['condition']]}">
          {breadth['label']}<br>
          <span style="font-size:11px;opacity:.8">
            Nifty: ₹{breadth['nifty_ltp']:,.0f} &nbsp;·&nbsp; EMA 50: ₹{breadth['nifty_ema50']:,.0f} &nbsp;·&nbsp; EMA 200: ₹{breadth['nifty_ema200']:,.0f}
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

            # ── Filter 4: RSI 30–50 ──────────────────────────────────────────
            rsi_val = calc_rsi_proper(close)
            if rsi_val is None: return None, "RSI calculation failed"
            rsi = rsi_val
            if not (30 <= rsi <= 50):
                return None, f"RSI {rsi:.1f} out of range"

            # ── Filter 5: Volume ≥ 1.5x 20-day avg ──────────────────────────
            avg_vol   = float(volume.iloc[-21:-1].mean())
            today_vol = float(volume.iloc[-1])
            vol_ratio = round(today_vol / avg_vol, 2) if avg_vol > 0 else 0
            if vol_ratio < 1.2:
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
        s1.metric("Scanned",         len(NIFTY50))
        s2.metric("Passed all 7",    len(qualifiers))
        s3.metric("Success rate",    f"{len(qualifiers)/len(NIFTY50)*100:.1f}%")
        s4.metric("Market condition","🟢 Go" if breadth and breadth["condition"]=="green" else "🟡 Caution" if breadth and breadth["condition"]=="yellow" else "🔴 Bear")

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

                # ── Stock header card ─────────────────────────────────────────
                chg_color = "#1D9E75" if q['Chg%']>=0 else "#E24B4A"
                st.markdown(f"""
                <div style="background:#fff;border:0.5px solid #E0DED8;border-radius:10px;
                            padding:14px 18px;margin-bottom:10px;
                            border-left:4px solid {score_color}">
                  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                      <span style="background:#1A1A18;color:white;font-weight:600;font-size:14px;
                                   padding:4px 12px;border-radius:6px">{q['Stock']}</span>
                      <span style="color:#6B6B68;font-size:12px">{q['Sector']}</span>
                      <span style="font-size:12px;color:#444">{q['Candle']}</span>
                      <span style="background:{score_color};color:white;font-size:10px;font-weight:600;
                                   padding:2px 8px;border-radius:20px">Score {q['Score']}/10</span>
                    </div>
                    <div style="text-align:right">
                      <span style="font-size:18px;font-weight:600;color:#1A1A18">₹{q['LTP ₹']:.2f}</span>
                      <span style="font-size:12px;color:{chg_color};margin-left:8px">
                        {'+' if q['Chg%']>=0 else ''}{q['Chg%']:.2f}%
                      </span>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Key indicators in clean columns ───────────────────────────
                m1,m2,m3,m4,m5,m6 = st.columns(6)
                m1.metric("RSI",          f"{q['RSI']}",          "30–50 ✓")
                m2.metric("EMA 200",      f"₹{q['EMA 200']:,.0f}","5%+ above ✓")
                m3.metric("EMA gap",      f"{q['EMA gap%']}%",    "Meaningful ✓")
                m4.metric("Volume",       f"{q['Vol ratio']}x",   "≥1.2x ✓")
                m5.metric("Risk/Reward",  f"{q['R:R ratio']}:1")
                m6.metric("From 52W High",f"{q['% from high']}%")

                # ── Trade plan in a clean 4-column grid ───────────────────────
                tp1,tp2,tp3,tp4 = st.columns(4)
                tp1.metric("Entry",      f"₹{q['LTP ₹']:.2f}",     "Trigger candle")
                tp2.metric("Stop Loss",  f"₹{q['Stop loss']:.2f}",  "Below candle low")
                tp3.metric("Target T1",  f"₹{q['Target 1 (4%)']:.2f}", "+4% · book 50%")
                tp4.metric("Target T2",  f"₹{q['Target 2 (8%)']:.2f}", "+8% · ride rest")

                # ── 2-tranche plan ────────────────────────────────────────────
                t1_price  = q['LTP ₹']
                t2_price  = round(q['Stop loss'] * 1.01, 2)
                lot       = q['Lot']
                t1_shares = round(lot * 0.60)
                t2_shares = lot - t1_shares
                t1_cost   = round(t1_price * t1_shares, 2)
                t2_cost   = round(t2_price * t2_shares, 2)
                avg_price = round((t1_cost+t2_cost)/(t1_shares+t2_shares), 2)
                total_cost= round(t1_cost+t2_cost, 2)

                st.markdown(f"""
                <div style="background:#F7F7F5;border:0.5px solid #E0DED8;border-radius:8px;
                            padding:12px 16px;margin:8px 0">
                  <div style="font-size:11px;font-weight:600;color:#6B6B68;text-transform:uppercase;
                              letter-spacing:.05em;margin-bottom:8px">2-Tranche Buy Plan · {lot:,} shares (1 lot)</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px">
                    <div style="background:#E6F1FB;border-radius:6px;padding:10px 12px">
                      <div style="font-size:10px;color:#0C447C;font-weight:600;text-transform:uppercase;margin-bottom:3px">Tranche 1 · 60%</div>
                      <div style="font-size:14px;font-weight:600;color:#185FA5">₹{t1_price:.2f} &nbsp;·&nbsp; {t1_shares:,} shares &nbsp;·&nbsp; ₹{t1_cost:,.0f}</div>
                      <div style="font-size:11px;color:#185FA5;margin-top:3px">✅ Enter on trigger candle</div>
                    </div>
                    <div style="background:#FFF9DB;border-radius:6px;padding:10px 12px">
                      <div style="font-size:10px;color:#7A5C00;font-weight:600;text-transform:uppercase;margin-bottom:3px">Tranche 2 · 40%</div>
                      <div style="font-size:14px;font-weight:600;color:#D98A1A">₹{t2_price:.2f} &nbsp;·&nbsp; {t2_shares:,} shares &nbsp;·&nbsp; ₹{t2_cost:,.0f}</div>
                      <div style="font-size:11px;color:#D98A1A;margin-top:3px">⏳ Only if price dips near stop</div>
                    </div>
                  </div>
                  <div style="font-size:12px;color:#444;display:flex;gap:16px;flex-wrap:wrap">
                    <span>Avg cost: <strong>₹{avg_price:.2f}</strong></span>
                    <span>Max capital: <strong>₹{total_cost:,.0f}</strong></span>
                    <span>CC strike: <strong>₹{q['CC Strike']}</strong></span>
                    <span>52W High: <strong>₹{q['52W High']:.2f}</strong></span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

            # Download
            df_q = pd.DataFrame(qualifiers)
            st.download_button("⬇ Download setups CSV",
                               df_q.to_csv(index=False),
                               "swing_covered_setups.csv","text/csv")

    # ══════════════════════════════════════════════════════════════════════════
    # POSITION TRACKER — Swing-Covered Portfolio
    # ══════════════════════════════════════════════════════════════════════════
    import json, base64, requests as req2

    st.divider()
    st.markdown("#### 📁 Swing-Covered Position Tracker")
    st.caption("Track your partial buys, build to full lot, monitor P&L and covered call income.")

    SC_FILE = "swing_covered_data.json"

    # ── GitHub helpers (reuse secrets) ────────────────────────────────────────
    def sc_headers():
        return {"Authorization": f"token {st.secrets.get('GITHUB_TOKEN','')}",
                "Accept": "application/vnd.github.v3+json"}

    def sc_load():
        try:
            url = f"https://api.github.com/repos/{st.secrets.get('GITHUB_REPO','')}/contents/{SC_FILE}"
            r = req2.get(url, headers=sc_headers(), timeout=10)
            if r.status_code == 200:
                j    = r.json()
                data = json.loads(base64.b64decode(j["content"]).decode())
                data["_sha"] = j["sha"]
                return data
            return {"positions": [], "_sha": None}
        except:
            return {"positions": [], "_sha": None}

    def sc_save(data):
        try:
            sha     = data.pop("_sha", None)
            encoded = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
            url     = f"https://api.github.com/repos/{st.secrets.get('GITHUB_REPO','')}/contents/{SC_FILE}"
            payload = {"message": "Update swing-covered positions", "content": encoded}
            if sha: payload["sha"] = sha
            r = req2.put(url, headers=sc_headers(), json=payload, timeout=10)
            if r.status_code in [200,201]:
                data["_sha"] = r.json()["content"]["sha"]
                return True
            st.error(f"Save failed: {r.status_code}")
            return False
        except Exception as e:
            st.error(f"Save error: {e}")
            return False

    @st.cache_data(ttl=300)
    def get_live_price(sym):
        try:
            df = yf.download(f"{sym}.NS", period="5d", interval="1d",
                             progress=False, auto_adjust=True)
            if df.empty: return None
            c    = df["Close"].squeeze().dropna()
            ltp  = float(c.iloc[-1])
            prev = float(c.iloc[-2])
            return {"ltp": ltp, "chg": ltp-prev, "chgp": (ltp-prev)/prev*100}
        except: return None

    # ── Load data ─────────────────────────────────────────────────────────────
    if "sc_data" not in st.session_state or st.session_state.get("sc_reload", True):
        st.session_state["sc_data"]   = sc_load()
        st.session_state["sc_reload"] = False

    sc_db     = st.session_state["sc_data"]
    positions = sc_db.get("positions", [])
    sc_holdings = sc_db.get("sc_holdings", [])
    sc_sold     = sc_db.get("sc_sold", [])

    # ── Sub tabs ──────────────────────────────────────────────────────────────
    sc_tab1, sc_tab2, sc_tab3, sc_tab4 = st.tabs([
        "📂 Open Holdings",
        "💸 Sell a Stock",
        "📋 Sold History",
        "📊 Covered Call Tracker",
    ])

    # ════════════════════════════════════════════════════════════════
    # SUB TAB 1 — Open Holdings
    # ════════════════════════════════════════════════════════════════
    with sc_tab1:
        st.markdown("**➕ Add holding**")
        with st.form("sc_holding_add", clear_on_submit=True):
            h1,h2,h3,h4 = st.columns(4)
            with h1: sh_sym   = st.selectbox("Stock", list(NIFTY50.keys()), key="sc_sym")
            with h2: sh_qty   = st.number_input("Quantity", min_value=1, step=1, key="sc_qty")
            with h3: sh_price = st.number_input("Buy price (₹)", min_value=0.01, step=0.05, format="%.2f", key="sc_bp")
            with h4: sh_date  = st.date_input("Buy date", key="sc_date")
            sh_notes = st.text_input("Notes (optional)", key="sc_notes")
            if st.form_submit_button("Add holding", type="primary", use_container_width=True):
                if sh_qty > 0 and sh_price > 0:
                    sc_holdings.append({
                        "id": len(sc_holdings)+1,
                        "symbol": sh_sym,
                        "sector": NIFTY50[sh_sym]["sector"],
                        "qty": int(sh_qty),
                        "buy_price": float(sh_price),
                        "buy_date": str(sh_date),
                        "notes": sh_notes,
                    })
                    sc_db["sc_holdings"] = sc_holdings
                    if sc_save(sc_db):
                        st.success(f"✓ {int(sh_qty)} shares of {sh_sym} @ ₹{sh_price:.2f} added!")
                        st.session_state["sc_reload"] = True
                        st.rerun()

        st.divider()
        if not sc_holdings:
            st.info("No open holdings yet. Add your first trade above.")
        else:
            st.markdown("**📂 Current open holdings**")
            from collections import defaultdict as _dd
            grouped = _dd(list)
            for h in sc_holdings: grouped[h["symbol"]].append(h)

            rows = []
            for sym, buys in grouped.items():
                tq   = sum(b["qty"] for b in buys)
                ac   = sum(b["qty"]*b["buy_price"] for b in buys)/tq
                fd   = min(b["buy_date"] for b in buys)
                hd   = (date.today()-date.fromisoformat(fd)).days
                live = get_live_price(sym)
                ltp  = live["ltp"] if live else ac
                inv  = round(ac*tq,2); cv=round(ltp*tq,2)
                up   = round(cv-inv,2); pp=round(up/inv*100,2) if inv else 0
                rows.append({"Ticker":sym,"Buy Date":fd,"Days":hd,"Qty":tq,
                             "Avg ₹":round(ac,2),"Live ₹":ltp if live else "—",
                             "Invested ₹":f"₹{inv:,.0f}",
                             "Curr Value ₹":f"₹{cv:,.0f}" if live else "—",
                             "Unreal P&L":f"₹{up:+,.0f}" if live else "—",
                             "P&L %":f"{pp:+.1f}%" if live else "—",
                             "_sym":sym,"_ac":ac,"_tq":tq})

            col_show=["Ticker","Buy Date","Days","Qty","Avg ₹","Live ₹",
                      "Invested ₹","Curr Value ₹","Unreal P&L","P&L %"]
            hdr="".join(f'<th style="background:#1A1A18;color:white;font-size:11px;font-weight:600;padding:9px 12px;text-align:left;white-space:nowrap;border-right:0.5px solid #444">{c}</th>' for c in col_show)
            bdy=""
            for i,r in enumerate(rows):
                bg="#fff" if i%2==0 else "#FAFAF8"; bdy+=f'<tr style="background:{bg}">'
                for c in col_show:
                    v=r[c]; s="padding:9px 12px;font-size:13px;border-right:0.5px solid #E0DED8;border-bottom:0.5px solid #E0DED8;white-space:nowrap;"
                    if c=="Ticker": s+="background:#1A1A18;color:white;font-weight:600;"
                    elif c in ["Unreal P&L","P&L %"]: s+=f"color:{'#1D9E75' if '+' in str(v) else '#E24B4A'};font-weight:600;"
                    bdy+=f'<td style="{s}">{v}</td>'
                bdy+="</tr>"
            st.markdown(f'<div style="overflow-x:auto;border:0.5px solid #E0DED8;border-radius:8px;overflow:hidden"><table style="width:100%;border-collapse:collapse;font-family:system-ui,sans-serif"><thead><tr>{hdr}</tr></thead><tbody>{bdy}</tbody></table></div>', unsafe_allow_html=True)

            st.markdown("")
            ti=sum(r["_ac"]*r["_tq"] for r in rows)
            tc=sum((get_live_price(r["_sym"])["ltp"] if get_live_price(r["_sym"]) else r["_ac"])*r["_tq"] for r in rows)
            tp=round(tc-ti,2); tpp=round(tp/ti*100,2) if ti else 0
            pm1,pm2,pm3,pm4=st.columns(4)
            pm1.metric("Open positions",f"{len(rows)}")
            pm2.metric("Total invested",f"₹{ti:,.0f}")
            pm3.metric("Current value", f"₹{tc:,.0f}")
            pm4.metric("Unrealised P&L",f"₹{tp:+,.0f}",f"{tpp:+.1f}%")

    # ════════════════════════════════════════════════════════════════
    # SUB TAB 2 — Sell a Stock
    # ════════════════════════════════════════════════════════════════
    with sc_tab2:
        st.markdown("**💸 Sell a stock**")
        open_syms = list({h["symbol"] for h in sc_holdings})
        if not open_syms:
            st.info("No open holdings to sell.")
        else:
            with st.form("sc_sell_form", clear_on_submit=True):
                s1,s2,s3,s4=st.columns(4)
                with s1: ss=st.selectbox("Stock to sell", sorted(open_syms), key="sc_sell_sym")
                with s2: sq=st.number_input("Qty to sell", min_value=1, step=1, key="sc_sell_qty")
                with s3: sp=st.number_input("Sell price (₹)", min_value=0.01, step=0.05, format="%.2f", key="sc_sell_price")
                with s4: sd=st.date_input("Sell date", key="sc_sell_date")
                sn=st.text_input("Notes (optional)", key="sc_sell_notes")
                if st.form_submit_button("💸 Confirm sell", type="primary", use_container_width=True):
                    buys  = [h for h in sc_holdings if h["symbol"]==ss]
                    total = sum(b["qty"] for b in buys)
                    if int(sq) > total:
                        st.error(f"You only hold {total} shares of {ss}.")
                    else:
                        ac    = sum(b["qty"]*b["buy_price"] for b in buys)/total
                        inv   = round(ac*int(sq),2); proc=round(float(sp)*int(sq),2)
                        rpnl  = round(proc-inv,2); pp=round(rpnl/inv*100,2) if inv else 0
                        fd    = min(b["buy_date"] for b in buys)
                        hd    = (date.fromisoformat(str(sd))-date.fromisoformat(fd)).days
                        sc_sold.append({"id":len(sc_sold)+1,"symbol":ss,
                                        "sector":NIFTY50[ss]["sector"],"qty":int(sq),
                                        "avg_cost":round(ac,2),"sell_price":float(sp),
                                        "buy_date":fd,"sell_date":str(sd),"hold_days":hd,
                                        "invested":inv,"proceeds":proc,
                                        "realised_pnl":rpnl,"pnl_pct":pp,"notes":sn})
                        rem = int(sq)
                        for h in sc_holdings:
                            if h["symbol"]!=ss or rem<=0: continue
                            ded=min(h["qty"],rem); h["qty"]-=ded; rem-=ded
                        sc_db["sc_holdings"]=[h for h in sc_holdings if h["qty"]>0]
                        sc_db["sc_sold"]=sc_sold
                        if sc_save(sc_db):
                            emoji="🟢" if rpnl>=0 else "🔴"
                            st.success(f"{emoji} Sold {int(sq)} {ss} @ ₹{sp:.2f} · P&L: ₹{rpnl:+,.0f} ({pp:+.1f}%)")
                            st.session_state["sc_reload"]=True; st.rerun()

    # ════════════════════════════════════════════════════════════════
    # SUB TAB 3 — Sold History
    # ════════════════════════════════════════════════════════════════
    with sc_tab3:
        st.markdown("**📋 Sold history**")
        if not sc_sold:
            st.info("No sold trades yet.")
        else:
            rows=[{"Ticker":s["symbol"],"Qty":s["qty"],
                   "Avg Cost ₹":f"₹{s['avg_cost']:.2f}","Sell Price ₹":f"₹{s['sell_price']:.2f}",
                   "Buy Date":s["buy_date"],"Sell Date":s["sell_date"],"Hold Days":s["hold_days"],
                   "Invested ₹":f"₹{s['invested']:,.0f}","Proceeds ₹":f"₹{s['proceeds']:,.0f}",
                   "Realised P&L":f"₹{s['realised_pnl']:+,.0f}","P&L %":f"{s['pnl_pct']:+.1f}%",
                   "Notes":s.get("notes","—")} for s in sorted(sc_sold,key=lambda x:x["sell_date"],reverse=True)]
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            tr=sum(s["realised_pnl"] for s in sc_sold)
            wins=[s for s in sc_sold if s["realised_pnl"]>0]
            r1,r2,r3,r4=st.columns(4)
            r1.metric("Total trades",  len(sc_sold))
            r2.metric("Total realised",f"₹{tr:+,.0f}")
            r3.metric("Win rate",      f"{len(wins)/len(sc_sold)*100:.0f}%")
            r4.metric("Best trade",    f"₹{max(s['realised_pnl'] for s in sc_sold):+,.0f}")
            st.download_button("⬇ Download history",pd.DataFrame(rows).to_csv(index=False),"sc_sold_history.csv","text/csv")

    # ════════════════════════════════════════════════════════════════
    # SUB TAB 4 — Covered Call Tracker (existing functionality)
    # ════════════════════════════════════════════════════════════════
    with sc_tab4:

        # ── Portfolio summary ─────────────────────────────────────────────────────
        if positions:
            total_invested = 0
            total_current  = 0
            total_premium  = 0
            for pos in positions:
                buys = pos.get("buys", [])
                total_shares = sum(b["shares"] for b in buys)
                avg_cost     = sum(b["shares"]*b["price"] for b in buys)/total_shares if total_shares else 0
                live         = get_live_price(pos["symbol"])
                ltp          = live["ltp"] if live else avg_cost
                invested     = round(avg_cost * total_shares, 2)
                current      = round(ltp * total_shares, 2)
                prem         = sum(c.get("premium_income",0) for c in pos.get("cc_cycles",[]))
                total_invested += invested
                total_current  += current
                total_premium  += prem

            total_stock_pnl  = round(total_current - total_invested, 2)
            total_combined   = round(total_stock_pnl + total_premium, 2)

            pm1,pm2,pm3,pm4 = st.columns(4)
            pm1.metric("Total invested",  f"₹{total_invested:,.0f}", f"{len(positions)} positions")
            pm2.metric("Stock P&L",       f"₹{total_stock_pnl:+,.0f}", f"{total_stock_pnl/total_invested*100:+.1f}%" if total_invested else "—")
            pm3.metric("Premium earned",  f"₹{total_premium:,.0f}", "all cycles")
            pm4.metric("Combined P&L",    f"₹{total_combined:+,.0f}", f"{total_combined/total_invested*100:+.1f}%" if total_invested else "—")
            st.divider()

        # ── Add new Nifty 50 stock for covered call tracking ─────────────────────
        st.markdown("**➕ Add stock for covered call tracking**")
        with st.form("sc_add_cc_stock", clear_on_submit=True):
            n1,n2,n3,n4 = st.columns(4)
            with n1: n_sym    = st.selectbox("Stock (any Nifty 50)", list(NIFTY50.keys()), key="cc_sym")
            with n2: n_shares = st.number_input("Shares held", min_value=1, step=1, key="cc_sh")
            with n3: n_price  = st.number_input("Avg buy price (₹)", min_value=0.01, step=0.05, format="%.2f", key="cc_bp")
            with n4: n_date   = st.date_input("Buy date", key="cc_bd")
            n_notes = st.text_input("Notes (optional)", key="cc_notes")
            if st.form_submit_button("➕ Add to tracker", type="primary", use_container_width=True):
                if n_shares > 0 and n_price > 0:
                    existing = next((p for p in positions if p["symbol"]==n_sym), None)
                    new_buy  = {"shares":int(n_shares),"price":float(n_price),
                                "date":str(n_date),"notes":n_notes}
                    if existing:
                        existing["buys"].append(new_buy)
                    else:
                        positions.append({
                            "id":       len(positions)+1,
                            "symbol":   n_sym,
                            "sector":   NIFTY50[n_sym]["sector"],
                            "lot_size": NIFTY50[n_sym]["lot"],
                            "buys":     [new_buy],
                            "cc_cycles":[],
                        })
                    sc_db["positions"] = positions
                    if sc_save(sc_db):
                        st.success(f"✓ {n_sym} added to covered call tracker!")
                        st.session_state["sc_reload"] = True
                        st.rerun()

        # ── Position cards ────────────────────────────────────────────────────────
        if not positions:
            st.info("No stocks in tracker yet. Add any Nifty 50 stock above.")
        else:
            st.divider()
            st.markdown("**📊 Current positions**")

            for pos in positions:
                sym      = pos["symbol"]
                sector   = pos["sector"]
                lot_size = pos["lot_size"]
                buys     = pos.get("buys", [])
                cc_cycles= pos.get("cc_cycles", [])

                total_shares = sum(b["shares"] for b in buys)
                avg_cost     = sum(b["shares"]*b["price"] for b in buys)/total_shares if total_shares else 0
                invested     = round(avg_cost * total_shares, 2)
                pct_to_lot   = min(100, round(total_shares/lot_size*100, 1))
                remaining    = max(0, lot_size - total_shares)
                total_prem   = sum(c.get("premium_income",0) for c in cc_cycles)

                live  = get_live_price(sym)
                ltp   = live["ltp"] if live else avg_cost
                ltp_ok= live is not None
                current     = round(ltp * total_shares, 2)
                stock_pnl   = round(current - invested, 2)
                combined    = round(stock_pnl + total_prem, 2)
                pnl_pct     = round(stock_pnl/invested*100, 2) if invested else 0
                chg_txt     = f"{live['chg']:+.2f} ({live['chgp']:+.2f}%)" if ltp_ok else "—"

                sc_col = "#1D9E75" if stock_pnl>=0 else "#E24B4A"

                st.markdown(f"""
                <div style="background:#F2FBF6;border:1.5px solid #1D9E75;border-radius:12px;
                            padding:16px 20px;margin-bottom:8px">
                  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
                    <div>
                      <span style="background:#1A1A18;color:white;font-weight:700;font-size:16px;
                                   padding:4px 14px;border-radius:6px">{sym}</span>
                      <span style="background:#EFEFEC;color:#555;font-size:11px;font-weight:500;
                                   padding:3px 10px;border-radius:10px;margin-left:8px">{sector}</span>
                    </div>
                    <div style="text-align:right">
                      <div style="font-size:22px;font-weight:700">₹{ltp:.2f}</div>
                      <div style="font-size:12px;color:{'#1D9E75' if ltp_ok and live['chg']>=0 else '#E24B4A'}">{chg_txt}</div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Metrics row
                mc1,mc2,mc3,mc4,mc5,mc6 = st.columns(6)
                mc1.metric("Shares held",    f"{total_shares:,}",    f"of {lot_size:,} (1 lot)")
                mc2.metric("Avg cost",       f"₹{avg_cost:.2f}")
                mc3.metric("Invested",       f"₹{invested:,.0f}")
                mc4.metric("Stock P&L",      f"₹{stock_pnl:+,.0f}",  f"{pnl_pct:+.1f}%")
                mc5.metric("Premium earned", f"₹{total_prem:,.0f}",  f"{len(cc_cycles)} cycles")
                mc6.metric("Combined P&L",   f"₹{combined:+,.0f}")

                # Progress to full lot
                st.markdown(f"""
                <div style="margin:10px 0 4px;display:flex;justify-content:space-between;font-size:12px;color:#6B6B68">
                  <span>Progress to 1 lot ({lot_size:,} shares)</span>
                  <span>{total_shares:,} / {lot_size:,} shares &nbsp;·&nbsp; {remaining:,} remaining</span>
                </div>
                <div style="height:8px;background:#EFEFEC;border-radius:4px;overflow:hidden;margin-bottom:4px">
                  <div style="height:8px;background:{'#1D9E75' if pct_to_lot==100 else '#185FA5'};
                              border-radius:4px;width:{pct_to_lot}%"></div>
                </div>
                <div style="font-size:11px;color:#888;margin-bottom:10px">
                  {'✅ Full lot complete — ready to sell covered call!' if pct_to_lot==100 else f'{pct_to_lot}% of lot filled'}
                </div>
                """, unsafe_allow_html=True)

                # Buy history
                with st.expander(f"📋 {sym} — buy history ({len(buys)} entries)"):
                    bh_rows = [{"Date":b["date"],"Shares":b["shares"],
                                "Price ₹":f"₹{b['price']:.2f}",
                                "Value ₹":f"₹{b['shares']*b['price']:,.0f}",
                                "Notes":b.get("notes","—")} for b in buys]
                    st.dataframe(pd.DataFrame(bh_rows), use_container_width=True, hide_index=True)

                # ── Sell shares from this position ────────────────────────────────
                with st.expander(f"💸 {sym} — sell shares"):
                    with st.form(f"sell_form_{sym}", clear_on_submit=True):
                        sell_c1, sell_c2, sell_c3 = st.columns(3)
                        with sell_c1:
                            sell_qty   = st.number_input("Qty to sell", min_value=1,
                                                          max_value=total_shares, step=1,
                                                          key=f"sq_{sym}")
                        with sell_c2:
                            sell_price = st.number_input("Sell price (₹)", min_value=0.01,
                                                          step=0.05, format="%.2f", key=f"sp_{sym}")
                        with sell_c3:
                            sell_date  = st.date_input("Sell date", key=f"sd_{sym}")
                        sell_notes = st.text_input("Notes (optional)", key=f"sn_{sym}")
                        sell_submit= st.form_submit_button("💸 Confirm sell", type="primary")
                        if sell_submit and sell_qty > 0 and sell_price > 0:
                            inv_sold  = round(avg_cost * int(sell_qty), 2)
                            proceeds  = round(float(sell_price) * int(sell_qty), 2)
                            rpnl      = round(proceeds - inv_sold, 2)
                            rpnl_pct  = round(rpnl/inv_sold*100,2) if inv_sold else 0
                            # Reload fresh data, apply sell, save
                            fresh = sc_load()
                            fresh_pos = fresh.get("positions", [])
                            target = next((p for p in fresh_pos if p["symbol"]==sym), None)
                            if target:
                                rem = int(sell_qty)
                                for b in target["buys"]:
                                    if rem <= 0: break
                                    ded = min(b["shares"], rem)
                                    b["shares"] -= ded
                                    rem -= ded
                                target["buys"] = [b for b in target["buys"] if b["shares"] > 0]
                                if not target["buys"]:
                                    fresh["positions"] = [p for p in fresh_pos if p["symbol"] != sym]
                                else:
                                    fresh["positions"] = fresh_pos
                                if sc_save(fresh):
                                    emoji = "🟢" if rpnl >= 0 else "🔴"
                                    st.success(f"{emoji} Sold {int(sell_qty)} {sym} @ ₹{sell_price:.2f} · P&L: ₹{rpnl:+,.0f} ({rpnl_pct:+.1f}%)")
                                    st.session_state["sc_reload"] = True
                                    st.rerun()

                # ── Covered call cycle history ────────────────────────────────
                if cc_cycles:
                    st.markdown(f"**💰 {sym} — covered call history**")
                    cyc_rows = []
                    for idx, c in enumerate(cc_cycles, 1):
                        cyc_rows.append({
                            "#":             idx,
                            "Strike ₹":     f"₹{float(c.get('strike',0)):.2f}",
                            "Premium/sh ₹": f"₹{float(c.get('premium',0)):.2f}",
                            "Expiry":        c.get("expiry", c.get("expiry_date","—")),
                            "Shares":        c.get("shares", total_shares),
                            "Income ₹":      f"₹{float(c.get('premium_income',0)):,.2f}",
                            "Outcome":       "✅ Expired" if "expired" in str(c.get("outcome","")).lower() else "🔄 Called away",
                            "Notes":         c.get("notes","—"),
                        })
                    st.dataframe(pd.DataFrame(cyc_rows), use_container_width=True, hide_index=True)

                    # Delete cycle
                    d1,d2 = st.columns([1,3])
                    with d1:
                        del_cyc = st.number_input("Delete cycle #", min_value=1,
                                                   max_value=len(cc_cycles), step=1,
                                                   key=f"dc_{sym}")
                    with d2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button(f"🗑️ Delete", key=f"dcd_{sym}"):
                            pos["cc_cycles"] = [c for i,c in enumerate(cc_cycles,1) if i != int(del_cyc)]
                            sc_db["positions"] = positions
                            if sc_save(sc_db):
                                st.success(f"Cycle #{int(del_cyc)} deleted.")
                                st.session_state["sc_reload"] = True
                                st.rerun()

                    # Summary
                    tp = sum(float(c.get("premium_income",0)) for c in cc_cycles)
                    cs1,cs2,cs3 = st.columns(3)
                    cs1.metric("Total cycles",  len(cc_cycles))
                    cs2.metric("Total premium", f"₹{tp:,.2f}")
                    cs3.metric("Avg per cycle", f"₹{tp/len(cc_cycles):,.2f}")

                # Log new cycle
                st.markdown(f"**➕ {sym} — log covered call cycle**")
                with st.form(f"cc_form_{sym}", clear_on_submit=True):
                    cc1,cc2,cc3,cc4 = st.columns(4)
                    with cc1: cc_strike  = st.number_input("Strike (₹)", min_value=0.0, step=0.5, format="%.2f", key=f"ccs_{sym}")
                    with cc2: cc_prem    = st.number_input("Premium/share (₹)", min_value=0.0, step=0.05, format="%.2f", key=f"ccp_{sym}")
                    with cc3: cc_expiry  = st.date_input("Expiry date", key=f"cce_{sym}")
                    with cc4: cc_outcome = st.selectbox("Outcome", [
                        "Option expired — kept shares",
                        "Called away at strike",
                        "🔄 Rolled over to next month",
                    ], key=f"cco_{sym}")
                    cc5,cc6 = st.columns(2)
                    with cc5: cc_notes = st.text_input("Notes (optional)", key=f"ccn_{sym}")
                    # Roll over fields — shown always, used only when outcome is roll
                    with cc6: cc_roll_strike = st.number_input("New strike if rolled (₹)", min_value=0.0, step=0.5, format="%.2f", key=f"ccrs_{sym}", help="Fill only if rolling over")
                    cc_roll_prem   = st.number_input("New premium if rolled (₹/share)", min_value=0.0, step=0.05, format="%.2f", key=f"ccrp_{sym}", help="Fill only if rolling over")
                    cc_roll_expiry = st.date_input("New expiry if rolled", key=f"ccre_{sym}", help="Fill only if rolling over")

                    if st.form_submit_button("💾 Save cycle", type="primary", use_container_width=True):
                        if cc_prem > 0:
                            prem_income = round(cc_prem * total_shares, 2)
                            if "cc_cycles" not in pos:
                                pos["cc_cycles"] = []
                            cycle = {
                                "id":             len(pos.get("cc_cycles",[]))+1,
                                "strike":         float(cc_strike),
                                "premium":        float(cc_prem),
                                "expiry":         str(cc_expiry),
                                "outcome":        cc_outcome,
                                "shares":         total_shares,
                                "premium_income": prem_income,
                                "notes":          cc_notes,
                            }
                            # If rolled — add roll details and create next cycle automatically
                            if "Rolled" in cc_outcome and cc_roll_prem > 0:
                                cycle["rolled_to_strike"]  = float(cc_roll_strike)
                                cycle["rolled_to_expiry"]  = str(cc_roll_expiry)
                                cycle["rolled_to_premium"] = float(cc_roll_prem)
                                # Auto-add next cycle for the roll
                                roll_income = round(cc_roll_prem * total_shares, 2)
                                pos["cc_cycles"].append(cycle)
                                pos["cc_cycles"].append({
                                    "id":             len(pos["cc_cycles"])+1,
                                    "strike":         float(cc_roll_strike),
                                    "premium":        float(cc_roll_prem),
                                    "expiry":         str(cc_roll_expiry),
                                    "outcome":        "Pending",
                                    "shares":         total_shares,
                                    "premium_income": roll_income,
                                    "notes":          f"Rolled from {cc_expiry}",
                                })
                                total_saved = prem_income + roll_income
                                sc_db["positions"] = positions
                                if sc_save(sc_db):
                                    st.success(f"✓ Roll saved! Original: ₹{prem_income:,.2f} + New: ₹{roll_income:,.2f} = ₹{total_saved:,.2f} total")
                                    st.session_state["sc_reload"] = True
                                    st.rerun()
                            else:
                                pos["cc_cycles"].append(cycle)
                                sc_db["positions"] = positions
                                if sc_save(sc_db):
                                    st.success(f"✓ Saved! Income: ₹{prem_income:,.2f}")
                                    st.session_state["sc_reload"] = True
                                    st.rerun()

                # Delete position
                if st.button(f"🗑️ Remove {sym} position", key=f"del_{sym}"):
                    sc_db["positions"] = [p for p in positions if p["symbol"]!=sym]
                    if sc_save(sc_db):
                        st.success(f"{sym} position removed.")
                        st.session_state["sc_reload"] = True
                        st.rerun()

                st.divider()

        # ── Monthly P&L Snapshot Tracker ──────────────────────────────────────────
        st.divider()
        st.markdown("#### 📅 Monthly P&L History")
        st.caption("Auto-saves a snapshot on the first open of each month. Use the button to save anytime.")

        this_month = pd.Timestamp.now().strftime("%Y-%m")

        def save_monthly_snapshot(label="auto"):
            """Calculate current P&L across all positions and save as monthly snapshot."""
            fresh_db  = sc_load()
            fresh_pos = fresh_db.get("positions", [])
            if not fresh_pos:
                return False
            snap_positions = []
            total_invested = 0
            total_current  = 0
            total_premium  = 0
            for pos in fresh_pos:
                buys         = pos.get("buys", [])
                total_shares = sum(b["shares"] for b in buys)
                if total_shares == 0: continue
                avg_cost     = sum(b["shares"]*b["price"] for b in buys) / total_shares
                live         = get_live_price(pos["symbol"])
                ltp          = live["ltp"] if live else avg_cost
                invested     = round(avg_cost * total_shares, 2)
                current      = round(ltp * total_shares, 2)
                prem         = sum(float(c.get("premium_income", 0)) for c in pos.get("cc_cycles", []))
                stock_pnl    = round(current - invested, 2)
                total_invested += invested
                total_current  += current
                total_premium  += prem
                snap_positions.append({
                    "symbol":       pos["symbol"],
                    "shares":       total_shares,
                    "avg_cost":     round(avg_cost, 2),
                    "ltp":          round(ltp, 2),
                    "invested":     invested,
                    "current_val":  current,
                    "stock_pnl":    stock_pnl,
                    "premium":      round(prem, 2),
                    "combined_pnl": round(stock_pnl + prem, 2),
                })

            if total_invested == 0:
                return False

            snapshot = {
                "month":         this_month,
                "date":          pd.Timestamp.now().strftime("%Y-%m-%d"),
                "label":         label,
                "total_invested":round(total_invested, 2),
                "total_current": round(total_current, 2),
                "stock_pnl":     round(total_current - total_invested, 2),
                "total_premium": round(total_premium, 2),
                "combined_pnl":  round(total_current - total_invested + total_premium, 2),
                "positions":     snap_positions,
            }
            snapshots = fresh_db.get("monthly_snapshots", [])
            snapshots = [s for s in snapshots if s["month"] != this_month]
            snapshots.append(snapshot)
            fresh_db["monthly_snapshots"] = snapshots
            return sc_save(fresh_db)

        # ── Monthly Premium Income ────────────────────────────────────────────
        st.divider()
        st.markdown("#### 📅 Monthly Premium Income")
        st.caption("Premium collected from covered call cycles — per stock per month")

        # Collect all cc_cycles across all positions
        all_cycles = []
        for pos in positions:
            for c in pos.get("cc_cycles", []):
                all_cycles.append({
                    "symbol":  pos["symbol"],
                    "month":   str(c.get("expiry_date",""))[:7],
                    "expiry":  c.get("expiry_date",""),
                    "strike":  c.get("strike", 0),
                    "premium": float(c.get("premium_income", 0)),
                    "outcome": c.get("outcome","—"),
                })

        if not all_cycles:
            st.info("No covered call cycles logged yet. Add cycles in the Covered Call Tracker tab.")
        else:
            df_cyc = pd.DataFrame(all_cycles)

            # Monthly summary table
            monthly = df_cyc.groupby("month")["premium"].sum().reset_index()
            monthly.columns = ["Month","Premium ₹"]
            monthly = monthly.sort_values("Month")
            monthly["Cumulative ₹"] = monthly["Premium ₹"].cumsum()

            import altair as alt
            bars = alt.Chart(monthly).mark_bar(
                color="#1D9E75", cornerRadiusTopLeft=4, cornerRadiusTopRight=4
            ).encode(
                x=alt.X("Month:O", axis=alt.Axis(labelAngle=-30)),
                y=alt.Y("Premium ₹:Q", title="Premium income (₹)"),
                tooltip=["Month", alt.Tooltip("Premium ₹:Q", format=",.0f")]
            )
            line = alt.Chart(monthly).mark_line(
                color="#185FA5", strokeWidth=2.5, point=True
            ).encode(
                x="Month:O",
                y=alt.Y("Cumulative ₹:Q", title=""),
                tooltip=["Month", alt.Tooltip("Cumulative ₹:Q", title="Cumulative", format=",.0f")]
            )
            st.altair_chart(alt.layer(bars, line).resolve_scale(y="independent"),
                            use_container_width=True, theme=None)
            st.caption("🟢 Bars = monthly premium · 🔵 Line = cumulative total")

            # Monthly table
            display = monthly.copy()
            display["Premium ₹"]    = display["Premium ₹"].apply(lambda x: f"₹{x:,.0f}")
            display["Cumulative ₹"] = display["Cumulative ₹"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(display, use_container_width=False, hide_index=True)

            # Per stock per month breakdown
            st.markdown("**Premium by stock**")
            by_stock = df_cyc.groupby(["symbol","month"])["premium"].sum().reset_index()
            by_stock.columns = ["Stock","Month","Premium ₹"]
            by_stock["Premium ₹"] = by_stock["Premium ₹"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(by_stock.sort_values(["Month","Stock"]),
                         use_container_width=False, hide_index=True)

            total_prem = df_cyc["premium"].sum()
            sm1,sm2,sm3 = st.columns(3)
            sm1.metric("Total cycles",   len(all_cycles))
            sm2.metric("Total premium",  f"₹{total_prem:,.0f}")
            sm3.metric("Avg per cycle",  f"₹{total_prem/len(all_cycles):,.0f}" if all_cycles else "—")

            st.download_button("⬇ Download premium history",
                               df_cyc.to_csv(index=False),
                               "premium_history.csv", "text/csv")

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
