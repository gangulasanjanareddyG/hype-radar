import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Hype Radar", layout="wide")

# -----------------------------
# 🌈 UI
# -----------------------------
st.markdown("""
<style>

/* Force readable text */
html, body, [class*="css"] {
    color: #222 !important;
}

/* Background */
.stApp {
    background: linear-gradient(-45deg, #fde2e4, #e2f0cb, #cdb4db, #a0e7e5);
    background-size: 400% 400%;
    animation: gradient 12s ease infinite;
}

/* Animation */
@keyframes gradient {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* Title */
.title {
    text-align:center;
    font-size:52px;
    font-weight:800;
    color:#ff4d88 !important;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.95);
    color: #222 !important;
    padding:20px;
    border-radius:20px;
    margin:15px 0;
    box-shadow:0 10px 25px rgba(0,0,0,0.1);
}

/* Recommendation colors */
.rec-buy { background:#d4edda; border-left:6px solid #28a745; }
.rec-emerging { background:#d0ebff; border-left:6px solid #339af0; }
.rec-watch { background:#fff3cd; border-left:6px solid #ffc107; }
.rec-overhyped { background:#ffe5d9; border-left:6px solid #ff922b; }
.rec-avoid { background:#f8d7da; border-left:6px solid #dc3545; }

/* Tags */
.tag {
    display:inline-block;
    padding:6px 12px;
    border-radius:12px;
    margin:5px;
    font-size:14px;
    color:#222 !important;
}

.trends { background:#ffd6e0; }
.reddit { background:#d0f4de; }
.youtube { background:#fff3b0; }
.news { background:#cdb4db; }

/* Badge */
.badge {
    display:inline-block;
    padding:6px 10px;
    border-radius:999px;
    margin-right:8px;
    font-size:12px;
    background:#f1f3f5;
    color:#222 !important;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv("enhanced_data.csv")

# -----------------------------
# HYPE SCORE
# -----------------------------
cols = ["trends_score", "reddit_score", "youtube_score", "news_score"]

df_z = df.copy()
for col in cols:
    df_z[col] = (df[col] - df[col].mean()) / df[col].std()

df_scaled = df_z.copy()
for col in cols:
    df_scaled[col] = 100 * (df_z[col] - df_z[col].min()) / (df_z[col].max() - df_z[col].min())

weights = {"trends_score":0.25, "reddit_score":0.20, "youtube_score":0.30, "news_score":0.25}

df_scaled["hype_score"] = sum(df_scaled[c]*w for c,w in weights.items())

df_scaled["consistency_std"] = df_scaled[cols].std(axis=1)

df_scaled["consistency_score"] = 100 * (1 - (df_scaled["consistency_std"] - df_scaled["consistency_std"].min()) /(df_scaled["consistency_std"].max() - df_scaled["consistency_std"].min()))

df_scaled["hype_score_adjusted"] = df_scaled["hype_score"]*0.90 + df_scaled["consistency_score"]*0.10

df = df_scaled

df["final_score"] = 0.7*df["hype_score_adjusted"] + 0.3*df["momentum_score"]

# -----------------------------
# HELPERS
# -----------------------------
def predict_label(row):
    if row["momentum_score"] > 65:
        return "🌱 Expected to grow"
    elif row["momentum_score"] < 35:
        return "📉 Losing momentum"
    return "➖ Likely stable"

def phase(row):
    if row["momentum_score"] > 70:
        return "🚀 Growth phase"
    elif row["momentum_score"] < 30:
        return "🧊 Decline phase"
    return "⚖️ Stable phase"

def top_driver(row):
    key = max(cols, key=lambda x: row[x])
    return key.replace("_score","").capitalize()

def confidence(row):
    spread = row[cols].std()
    if spread < 10:
        return "High"
    elif spread < 20:
        return "Medium"
    return "Low"

def reasoning(row):
    driver = top_driver(row)
    if row["momentum_score"] > 65:
        return f"Strong {driver} signal + rising momentum"
    elif row["momentum_score"] < 35:
        return f"Weak momentum despite {driver} activity"
    return f"Balanced signals led by {driver}"

# Recommendation Engine
def recommendation(row):
    hype = row["hype_score_adjusted"]
    momentum = row["momentum_score"]

    if momentum > 65:
        return "🚀 Buy Now", "Strong upward momentum → gaining popularity fast."
    elif momentum > 55:
        return "📈 Emerging", "Momentum is building → early growth stage."
    elif 40 <= momentum <= 55:
        return "👀 Watch Closely", "Stable interest → could go either way."
    elif momentum < 40 and hype > 55:
        return "⚠️ Overhyped", "Hype exists but interest is fading."
    else:
        return "❌ Avoid", "Low interest and weak momentum."

def rec_class(label):
    if "Buy" in label:
        return "rec-buy"
    elif "Emerging" in label:
        return "rec-emerging"
    elif "Watch" in label:
        return "rec-watch"
    elif "Overhyped" in label:
        return "rec-overhyped"
    return "rec-avoid"

# Context
context = {
    "iPhone 17": "Apple released iPhone 17 in Sept 2025 → spike, now cooling before next cycle.",
    "PS5 Pro": "Rumors + leaks drive spikes; each spec reveal boosts interest.",
    "Air Jordan 11": "Drop-driven hype → peaks at release, fades after.",
    "Owala FreeSip": "TikTok virality steadily increasing demand.",
    "Nvidia RTX 5090": "Pre-launch anticipation + performance leaks driving growth."
}

# Human Explanation
def human_explanation(row, product):
    rec, _ = recommendation(row)
    real = context.get(product, "")

    if "Buy" in rec:
        return f"People are suddenly paying a lot more attention to {product}. {real} This usually happens before something becomes very popular, so it's a good time to get in early."
    elif "Emerging" in rec:
        return f"{product} is starting to gain attention. {real} It's not huge yet, but clearly growing."
    elif "Watch" in rec:
        return f"{product} is steady right now. {real} Nothing major yet, so better to wait and watch."
    elif "Overhyped" in rec:
        return f"{product} already had a lot of attention, but now it's slowing down. {real} This usually means the trend is fading."
    else:
        return f"{product} is not getting much attention. {real} No strong sign of growth right now."

# Forecast

def forecast(series, steps=5):
    y = series.values
    x = np.arange(len(y))
    coef = np.polyfit(x, y, 1)
    future_x = np.arange(len(y), len(y)+steps)
    return coef[0]*future_x + coef[1]

# -----------------------------
# TITLE
# -----------------------------
st.markdown('<div class="title">🌈 Hype Radar</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center; font-size:18px;">Multi-Source Product Hype Intelligence System</div>', unsafe_allow_html=True)

# -----------------------------
# TOP TRENDING
# -----------------------------
st.subheader("🔥 Top Trending Right Now")
for _, r in df.sort_values(by="final_score", ascending=False).head(3).iterrows():
    st.markdown(f"<div class='card'><b>{r['product']}</b> — Score: {round(r['final_score'],1)}</div>", unsafe_allow_html=True)

# -----------------------------
# SELECT
# -----------------------------
selected = st.selectbox("Pick a product ✨", df["product"])
row = df[df["product"]==selected].iloc[0]

# -----------------------------
# MAIN CARD
# -----------------------------
st.markdown(f"""
<div class='card'>
<h2>{selected}</h2>
<p><b>Final Score:</b> {round(row['final_score'],1)}</p>
<p>🔥 Hype: {round(row['hype_score_adjusted'],1)} | ⚡ Momentum: {round(row['momentum_score'],1)}</p>
<p><b>{predict_label(row)}</b></p>
<p class='badge'>{phase(row)}</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# PREDICTION DETAIL
# -----------------------------
st.subheader("🔮 Prediction Breakdown")
conf = confidence(row)
reason = reasoning(row)

st.markdown(f"""
<div class='card'>
<b>{predict_label(row)}</b><br>
Confidence: <b>{conf}</b><br>
Reason: {reason}
</div>
""", unsafe_allow_html=True)

# -----------------------------
# RECOMMENDATION
# -----------------------------
st.subheader("🧭 What Should You Do?")
rec, rec_reason = recommendation(row)
rec_style = rec_class(rec)
human_text = human_explanation(row, selected)

st.markdown(f"""
<div class='card {rec_style}'>
<h3>{rec}</h3>
<p>{rec_reason}</p>
<br>
<p><b>🧠 Why this matters:</b> {human_text}</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# INSIGHT (ORIGINAL BACK)
# -----------------------------
st.subheader("🧠 Insight")

insight = f"{selected} is currently in a {phase(row).split()[1].lower()} with {top_driver(row)} driving most of the hype. "

if row["momentum_score"] > 65:
    insight += "Momentum is strong, suggesting continued growth. "
elif row["momentum_score"] < 35:
    insight += "Momentum is weak, indicating declining interest. "
else:
    insight += "Momentum is stable, with no major shifts expected. "

insight += context.get(selected, "")

st.markdown(f"<div class='card'>{insight}</div>", unsafe_allow_html=True)

# -----------------------------
# SIGNALS
# -----------------------------
st.subheader("📊 Signals")
st.markdown(f"""
<span class='tag trends'>🔍 {round(row['trends_score'],1)}</span>
<span class='tag reddit'>💬 {round(row['reddit_score'],1)}</span>
<span class='tag youtube'>🎥 {round(row['youtube_score'],1)}</span>
<span class='tag news'>📰 {round(row['news_score'],1)}</span>
""", unsafe_allow_html=True)

# -----------------------------
# BAR CHART
# -----------------------------
chart_df = pd.DataFrame({"Signal":["Trends","Reddit","YouTube","News"],"Score":[row[c] for c in cols]})
fig = px.bar(chart_df, x="Signal", y="Score", color="Signal")
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# TREND + FORECAST
# -----------------------------
st.subheader("📈 Trend + Forecast")
trends = pd.read_csv("google_trends.csv")
series = trends[selected]

fig = px.line(trends, x="date", y=selected)
future_vals = forecast(series.tail(20))
future_dates = pd.date_range(start=pd.to_datetime(trends['date']).iloc[-1], periods=len(future_vals)+1, freq='D')[1:]
fig.add_scatter(x=future_dates, y=future_vals, mode='lines', name='Forecast', line=dict(dash='dash'))

st.plotly_chart(fig, use_container_width=True)

st.write("Dashed line = short-term projection based on current trend.")
