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

html, body, [class*="css"] { color: #222 !important; }

.stApp {
    background: linear-gradient(-45deg, #fde2e4, #e2f0cb, #cdb4db, #a0e7e5);
    background-size: 400% 400%;
    animation: gradient 12s ease infinite;
}

@keyframes gradient {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

.title {
    text-align:center;
    font-size:52px;
    font-weight:800;
    color:#ff4d88 !important;
}

.card {
    background: rgba(255,255,255,0.95);
    padding:20px;
    border-radius:20px;
    margin:15px 0;
    box-shadow:0 10px 25px rgba(0,0,0,0.1);
}

.rec-buy { background:#d4edda; border-left:6px solid #28a745; }
.rec-emerging { background:#d0ebff; border-left:6px solid #339af0; }
.rec-watch { background:#fff3cd; border-left:6px solid #ffc107; }
.rec-overhyped { background:#ffe5d9; border-left:6px solid #ff922b; }
.rec-avoid { background:#f8d7da; border-left:6px solid #dc3545; }

.tag {
    display:inline-block;
    padding:6px 12px;
    border-radius:12px;
    margin:5px;
    font-size:14px;
}

.trends { background:#ffd6e0; }
.reddit { background:#d0f4de; }
.youtube { background:#fff3b0; }
.news { background:#cdb4db; }

.badge {
    display:inline-block;
    padding:6px 10px;
    border-radius:999px;
    margin-right:8px;
    font-size:12px;
    background:#f1f3f5;
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
# CONTEXT (REFINED)
# -----------------------------
def get_context(product):
    context_map = {
        "iPhone 17": (
            "Apple released the iPhone 17 around September 2025, which typically creates a spike in attention as people explore new features and compare upgrades. "
            "Now that the launch period has passed, interest is gradually settling as users begin waiting for the next iPhone cycle."
        ),
        "PS5 Pro": (
            "Interest in the PS5 Pro is largely driven by leaks, rumors, and performance expectations ahead of release. "
            "Each new detail about specs or gameplay improvements tends to bring more attention from gamers and tech enthusiasts."
        ),
        "Air Jordan 11": (
            "The Air Jordan 11 follows a drop-driven hype cycle, where attention peaks around release dates and limited restocks. "
            "Sneaker enthusiasts closely track these drops, which leads to sharp spikes in interest followed by gradual cooling."
        ),
        "Owala FreeSip": (
            "The Owala FreeSip has been gaining popularity through social media, especially short-form content where people share everyday use and design features. "
            "This kind of organic visibility often leads to steady and consistent growth in attention."
        ),
        "Nvidia RTX 5090": (
            "The RTX 5090 is building attention ahead of its official release, driven by performance leaks, benchmarks, and speculation within the tech community. "
            "Pre-launch anticipation like this typically leads to rising interest as more information becomes available."
        )
    }
    return context_map.get(product, "There are no clear external events driving attention at the moment.")

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
    return key.replace("_score", "").capitalize()


def confidence(row):
    spread = row[cols].std()
    if spread < 10:
        return "High"
    elif spread < 20:
        return "Medium"
    return "Low"


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


def human_explanation(row, product):
    rec, _ = recommendation(row)
    real = get_context(product)

    if "Buy" in rec:
        return (
            f"{product} is clearly gaining attention right now. {real} This kind of pattern usually shows up when something is starting to take off, with more people discovering it and engaging with it."
        )

    elif "Emerging" in rec:
        return (
            f"{product} is beginning to build momentum. {real} It’s not at peak popularity yet, but interest is steadily growing, which often signals an early growth phase."
        )

    elif "Watch" in rec:
        return (
            f"{product} is relatively stable at the moment. {real} There’s some activity, but nothing strong enough yet to indicate a clear direction."
        )

    elif "Overhyped" in rec:
        return (
            f"{product} already experienced strong attention earlier. {real} Now the momentum is slowing down, which typically happens after the initial excitement fades."
        )

    else:
        return (
            f"{product} is not seeing much attention right now. {real} There are no strong signals suggesting growth, so it’s likely staying in a low-interest phase."
        )


def generate_insight(row, product):
    driver = top_driver(row)
    real = get_context(product)

    if row["momentum_score"] > 65:
        trend = "Interest is picking up quickly"
    elif row["momentum_score"] < 35:
        trend = "Interest is starting to slow down"
    else:
        trend = "Interest is fairly steady right now"

    return (
        f"{trend} for {product}, with most of the attention coming from {driver.lower()} activity. {real}"
    )


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

st.markdown(f"""
<div class='card'>
<b>{predict_label(row)}</b><br>
Confidence: <b>{conf}</b>
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
<p><b>Why this matters:</b> {human_text}</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# INSIGHT
# -----------------------------
st.subheader("🧠 Insight")
insight = generate_insight(row, selected)
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
.card {
    background: rgba(255,255,255,0.95);
    padding:20px;
    border-radius:20px;
    margin:15px 0;
    box-shadow:0 10px 25px rgba(0,0,0,0.1);
}

.rec-buy { background:#d4edda; border-left:6px solid #28a745; }
.rec-emerging { background:#d0ebff; border-left:6px solid #339af0; }
.rec-watch { background:#fff3cd; border-left:6px solid #ffc107; }
.rec-overhyped { background:#ffe5d9; border-left:6px solid #ff922b; }
.rec-avoid { background:#f8d7da; border-left:6px solid #dc3545; }

.tag {
    display:inline-block;
    padding:6px 12px;
    border-radius:12px;
    margin:5px;
    font-size:14px;
}

.trends { background:#ffd6e0; }
.reddit { background:#d0f4de; }
.youtube { background:#fff3b0; }
.news { background:#cdb4db; }

.badge {
    display:inline-block;
    padding:6px 10px;
    border-radius:999px;
    margin-right:8px;
    font-size:12px;
    background:#f1f3f5;
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
# CONTEXT (FINAL)
# -----------------------------
def get_context(product):
    context_map = {
        "iPhone 17": (
            "Apple released the iPhone 17 around September 2025, which typically creates a spike in attention as people explore new features and compare upgrades. "
            "Now that the launch period has passed, interest is gradually settling as users begin waiting for the next iPhone cycle."
        ),
        "PS5 Pro": (
            "Interest in the PS5 Pro is largely driven by leaks, rumors, and performance expectations ahead of release. "
            "Each new detail about specs or gameplay improvements tends to bring more attention from gamers and tech enthusiasts."
        ),
        "Air Jordan 11": (
            "The Air Jordan 11 follows a drop-driven hype cycle, where attention peaks around release dates and limited restocks. "
            "Sneaker enthusiasts closely track these drops, which leads to sharp spikes in interest followed by gradual cooling."
        ),
        "Owala FreeSip": (
            "The Owala FreeSip has been gaining popularity through social media, especially short-form content where people share everyday use and design features. "
            "This kind of organic visibility often leads to steady and consistent growth in attention."
        ),
        "Nvidia RTX 5090": (
            "The RTX 5090 is building attention ahead of its official release, driven by performance leaks, benchmarks, and speculation within the tech community. "
            "Pre-launch anticipation like this typically leads to rising interest as more information becomes available."
        )
    }
    return context_map.get(product, "There are no clear external events driving attention at the moment.")

# -----------------------------
# HELPERS
# -----------------------------
def predict_label(row):
    if row["momentum_score"] > 65:
        return "Expected to grow"
    elif row["momentum_score"] < 35:
        return "Losing momentum"
    return "Likely stable"


def phase(row):
    if row["momentum_score"] > 70:
        return "Growth phase"
    elif row["momentum_score"] < 30:
        return "Decline phase"
    return "Stable phase"


def top_driver(row):
    key = max(cols, key=lambda x: row[x])
    return key.replace("_score",""
).capitalize()


def confidence(row):
    spread = row[cols].std()
    if spread < 10:
        return "High"
    elif spread < 20:
        return "Medium"
    return "Low"


def recommendation(row):
    hype = row["hype_score_adjusted"]
    momentum = row["momentum_score"]

    if momentum > 65:
        return "Buy Now", "Strong upward momentum"
    elif momentum > 55:
        return "Emerging", "Momentum is building"
    elif 40 <= momentum <= 55:
        return "Watch Closely", "Stable interest"
    elif momentum < 40 and hype > 55:
        return "Overhyped", "Hype exists but fading"
    else:
        return "Avoid", "Low interest"


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


def human_explanation(row, product):
    rec, _ = recommendation(row)
    real = get_context(product)

    if "Buy" in rec:
        return f"{product} is clearly gaining attention right now. {real} This usually happens when something is about to take off."
    elif "Emerging" in rec:
        return f"{product} is starting to build momentum. {real} Interest is growing steadily."
    elif "Watch" in rec:
        return f"{product} is relatively stable right now. {real} It could move in either direction."
    elif "Overhyped" in rec:
        return f"{product} had strong attention earlier. {real} Now momentum is slowing down."
    else:
        return f"{product} is not getting much attention. {real}"


def generate_insight(row, product):
    driver = top_driver(row)
    real = get_context(product)

    if row["momentum_score"] > 65:
        trend = "Interest is picking up quickly"
    elif row["momentum_score"] < 35:
        trend = "Interest is starting to slow down"
    else:
        trend = "Interest is fairly steady"

    return f"{trend} for {product}, mainly driven by {driver.lower()} activity. {real}"


def forecast(series, steps=5):
    y = series.values
    x = np.arange(len(y))
    coef = np.polyfit(x, y, 1)
    future_x = np.arange(len(y), len(y)+steps)
    return coef[0]*future_x + coef[1]

# -----------------------------
# UI
# -----------------------------
st.markdown('<div class="title">Hype Radar</div>', unsafe_allow_html=True)

st.subheader("Top Trending")
for _, r in df.sort_values(by="final_score", ascending=False).head(3).iterrows():
    st.markdown(f"<div class='card'><b>{r['product']}</b> — Score: {round(r['final_score'],1)}</div>", unsafe_allow_html=True)

selected = st.selectbox("Pick a product", df["product"])
row = df[df["product"]==selected].iloc[0]

st.markdown(f"""
<div class='card'>
<h2>{selected}</h2>
<p>Final Score: {round(row['final_score'],1)}</p>
<p>Hype: {round(row['hype_score_adjusted'],1)} | Momentum: {round(row['momentum_score'],1)}</p>
<p>{predict_label(row)}</p>
<p class='badge'>{phase(row)}</p>
</div>
""", unsafe_allow_html=True)

st.subheader("Prediction")
st.markdown(f"<div class='card'>{predict_label(row)} | Confidence: {confidence(row)}</div>", unsafe_allow_html=True)

st.subheader("Recommendation")
rec, rec_reason = recommendation(row)
st.markdown(f"<div class='card {rec_class(rec)}'><h3>{rec}</h3><p>{rec_reason}</p><p>{human_explanation(row, selected)}</p></div>", unsafe_allow_html=True)

st.subheader("Insight")
insight = generate_insight(row, selected)
st.markdown(f"<div class='card'>{insight}</div>", unsafe_allow_html=True)

st.subheader("Signals")
st.write(row[cols])

chart_df = pd.DataFrame({"Signal":["Trends","Reddit","YouTube","News"],"Score":[row[c] for c in cols]})
fig = px.bar(chart_df, x="Signal", y="Score", color="Signal")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Trend + Forecast")
trends = pd.read_csv("google_trends.csv")
series = trends[selected]

fig = px.line(trends, x="date", y=selected)
future_vals = forecast(series.tail(20))
future_dates = pd.date_range(start=pd.to_datetime(trends['date']).iloc[-1], periods=len(future_vals)+1, freq='D')[1:]
fig.add_scatter(x=future_dates, y=future_vals, mode='lines', name='Forecast', line=dict(dash='dash'))

st.plotly_chart(fig, use_container_width=True)

st.write("Dashed line = short-term projection based on current trend.")
