import ast
import glob
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Movie IQ — Film Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# CUSTOM CSS
# ----------------------------------------------------------------------------
st.markdown("""
    <style>
    .main-title {
        font-size: 40px;
        font-weight: 800;
        text-align: left;
        background: linear-gradient(90deg, #6D5DFC, #4D96FF, #4DCCBD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: left;
        color: #9AA0A6;
        font-size: 16px;
        margin-top: 4px;
        margin-bottom: 10px;
    }
    .kpi-card {
        border-radius: 14px;
        padding: 18px 14px;
        text-align: left;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.18);
        margin-bottom: 10px;
    }
    .kpi-value { font-size: 26px; font-weight: 800; margin: 0px; }
    .kpi-label { font-size: 13px; font-weight: 500; opacity: 0.9; margin: 0px; }
    .section-header {
        font-size: 22px;
        font-weight: 700;
        margin-top: 22px;
        margin-bottom: 10px;
        border-left: 6px solid #6D5DFC;
        padding-left: 12px;
    }
    .insight-box {
        background-color: rgba(107, 203, 119, 0.10);
        border-left: 5px solid #6BCB77;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 15px;
    }
    .rec-box {
        background-color: rgba(77, 150, 255, 0.10);
        border-left: 5px solid #4D96FF;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 15px;
    }
    .greenlight-box {
        border-radius: 14px;
        padding: 22px;
        color: white;
        text-align: center;
        font-size: 20px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# DATA LOADING & CLEANING
# ----------------------------------------------------------------------------
def find_csv():
    """Locate the movie dataset even if the filename got altered (e.g. 'movies (3).csv')."""
    if os.path.exists("movies.csv"):
        return "movies.csv"
    candidates = glob.glob("movies*.csv") + glob.glob("*.csv")
    return candidates[0] if candidates else None


@st.cache_data
def load_data():
    path = find_csv()
    if path is None:
        st.error("Could not find a CSV file in this folder. Please make sure 'movies.csv' is uploaded alongside app.py.")
        st.stop()
    df = pd.read_csv(path)

    df.columns = [c.strip() for c in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    df = df.drop_duplicates()

    numeric_cols = ["budget", "revenue", "popularity", "runtime", "vote_average"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in numeric_cols:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    df["title"] = df["title"].fillna("Unknown")
    df["genres"] = df["genres"].fillna("Unknown")

    df = df[(df["budget"] >= 0) & (df["revenue"] >= 0)]

    def extract_genre(g):
        try:
            parsed = ast.literal_eval(g)
            if isinstance(parsed, list) and len(parsed) > 0:
                names = [d.get("name", "Unknown") for d in parsed if isinstance(d, dict)]
                return names[0] if names else "Unknown"
            return "Unknown"
        except (ValueError, SyntaxError):
            return "Unknown"

    df["genre_clean"] = df["genres"].apply(extract_genre)

    # Feature engineering
    df["profit"] = df["revenue"] - df["budget"]
    df["roi"] = np.where(df["budget"] > 0, (df["profit"] / df["budget"]) * 100, np.nan)
    df["profitable"] = df["profit"] > 0

    def budget_bucket(b):
        if b < 10_000_000:
            return "Micro/Indie (<$10M)"
        elif b < 50_000_000:
            return "Mid-Budget ($10M-$50M)"
        elif b < 100_000_000:
            return "High-Budget ($50M-$100M)"
        else:
            return "Blockbuster (>$100M)"

    df["budget_category"] = df["budget"].apply(budget_bucket)

    df = df.reset_index(drop=True)
    return df


df = load_data()

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
h1, h2 = st.columns([5, 1])
with h1:
    st.markdown('<p class="main-title">🎬 Movie IQ — Film Analytics Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Interactive financial modeling, ROI analysis, and box office insights for producers</p>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------------------------------
st.sidebar.markdown("### 🎬 Movie IQ Studio")
st.sidebar.caption("Interactive Film Business Intelligence")
st.sidebar.markdown("---")

all_genres = sorted(df["genre_clean"].unique())
selected_genres = st.sidebar.multiselect("Select Genres", options=all_genres, default=all_genres)

budget_cats = ["Micro/Indie (<$10M)", "Mid-Budget ($10M-$50M)", "High-Budget ($50M-$100M)", "Blockbuster (>$100M)"]
selected_budget_cats = st.sidebar.multiselect("Budget Category", options=budget_cats, default=budget_cats)

outcome = st.sidebar.radio("Box Office Outcome", options=["All Movies", "Profitable Only", "Flop/Loss Only"])

runtime_min, runtime_max = int(df["runtime"].min()), int(df["runtime"].max())
selected_runtime = st.sidebar.slider("Runtime Range (minutes)", min_value=runtime_min, max_value=runtime_max,
                                      value=(runtime_min, runtime_max))

search_title = st.sidebar.text_input("🔍 Search Film Title", "")

st.sidebar.markdown("---")
st.sidebar.caption("Made with ❤️ using Streamlit")

# Apply filters
filtered_df = df[
    (df["genre_clean"].isin(selected_genres)) &
    (df["budget_category"].isin(selected_budget_cats)) &
    (df["runtime"].between(selected_runtime[0], selected_runtime[1]))
]
if outcome == "Profitable Only":
    filtered_df = filtered_df[filtered_df["profitable"]]
elif outcome == "Flop/Loss Only":
    filtered_df = filtered_df[~filtered_df["profitable"]]
if search_title.strip():
    filtered_df = filtered_df[filtered_df["title"].str.contains(search_title.strip(), case=False, na=False)]

if filtered_df.empty:
    st.warning("⚠️ No movies match the selected filters. Please adjust your filter selection.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI CARDS
# ----------------------------------------------------------------------------
def fmt_money(x):
    if x >= 1e9:
        return f"${x/1e9:.2f}B"
    elif x >= 1e6:
        return f"${x/1e6:.1f}M"
    elif x >= 1e3:
        return f"${x/1e3:.1f}K"
    return f"${x:.0f}"

total_movies = len(filtered_df)
avg_budget = filtered_df["budget"].mean()
avg_revenue = filtered_df["revenue"].mean()
success_rate = filtered_df["profitable"].mean() * 100
avg_roi = filtered_df["roi"].mean()

kpi_data = [
    ("Selected Movies", f"{total_movies:,}", "linear-gradient(135deg,#6D5DFC,#4D96FF)"),
    ("Avg Budget", fmt_money(avg_budget), "linear-gradient(135deg,#4D96FF,#4DCCBD)"),
    ("Avg Revenue", fmt_money(avg_revenue), "linear-gradient(135deg,#4DCCBD,#6BCB77)"),
    ("Success Rate", f"{success_rate:.1f}%", "linear-gradient(135deg,#FF8C42,#FFD93D)"),
    ("Avg ROI", f"{avg_roi:.1f}%", "linear-gradient(135deg,#FF4B4B,#FF8C42)"),
]
cols = st.columns(len(kpi_data))
for col, (label, value, gradient) in zip(cols, kpi_data):
    col.markdown(f"""
        <div class="kpi-card" style="background:{gradient};">
            <p class="kpi-value">{value}</p>
            <p class="kpi-label">{label}</p>
        </div>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------------
tab_overview, tab_compare, tab_sim, tab_genre, tab_explore = st.tabs([
    "📈 Executive Overview", "🎯 Movie Comparison", "💡 Greenlight Simulator",
    "📊 Genre & Runtime Insights", "📁 Smart Data Explorer"
])

color_seq = px.colors.qualitative.Bold

# ---------------- TAB 1: EXECUTIVE OVERVIEW ----------------
with tab_overview:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Top 10 Revenue Movies")
        top10 = filtered_df.nlargest(10, "revenue").sort_values("revenue")
        fig = px.bar(top10, x="revenue", y="title", orientation="h", color="revenue",
                     color_continuous_scale="Sunset", labels={"revenue": "Revenue ($)", "title": ""})
        fig.update_layout(showlegend=False, height=400, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Budget vs Revenue")
        fig = px.scatter(filtered_df, x="budget", y="revenue", color="genre_clean",
                          size="popularity", hover_name="title",
                          labels={"budget": "Budget ($)", "revenue": "Revenue ($)", "genre_clean": "Genre"},
                          color_discrete_sequence=color_seq)
        fig.update_layout(height=400, legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Average Revenue by Genre")
        genre_rev = filtered_df.groupby("genre_clean")["revenue"].mean().sort_values(ascending=False).reset_index()
        fig = px.bar(genre_rev, x="genre_clean", y="revenue", color="genre_clean",
                     color_discrete_sequence=color_seq, labels={"genre_clean": "Genre", "revenue": "Avg Revenue ($)"})
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("Profitable vs Loss-Making Movies")
        outcome_count = filtered_df["profitable"].map({True: "Profitable", False: "Flop/Loss"}).value_counts().reset_index()
        outcome_count.columns = ["outcome", "count"]
        fig = px.pie(outcome_count, names="outcome", values="count", hole=0.5,
                     color="outcome", color_discrete_map={"Profitable": "#6BCB77", "Flop/Loss": "#FF4B4B"})
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="section-header">💡 Business Insights</p>', unsafe_allow_html=True)
    top_genre_by_rev = filtered_df.groupby("genre_clean")["revenue"].mean().idxmax()
    corr_budget_rev = filtered_df["budget"].corr(filtered_df["revenue"])
    corr_pop_rev = filtered_df["popularity"].corr(filtered_df["revenue"])
    top_rated_movie = filtered_df.loc[filtered_df["vote_average"].idxmax(), "title"]
    highest_revenue_movie = filtered_df.loc[filtered_df["revenue"].idxmax(), "title"]

    insights = [
        f"🎬 <b>{highest_revenue_movie}</b> earns the highest revenue in the current selection.",
        f"🏆 <b>{top_genre_by_rev}</b> is the genre with the highest average revenue.",
        f"💰 Budget and revenue correlation is <b>{corr_budget_rev:.2f}</b> — "
        + ("higher budgets tend to drive higher revenue." if corr_budget_rev > 0.3 else "budget alone doesn't strongly predict revenue."),
        f"🔥 Popularity and revenue correlation is <b>{corr_pop_rev:.2f}</b> — "
        + ("more popular movies tend to earn more." if corr_pop_rev > 0.3 else "popularity alone doesn't guarantee higher revenue."),
        f"⭐ <b>{top_rated_movie}</b> holds the highest audience rating in this selection.",
        f"🎯 <b>{success_rate:.1f}%</b> of the selected movies were profitable (revenue > budget).",
    ]
    for ins in insights:
        st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)

    st.markdown('<p class="section-header">📌 Business Recommendations</p>', unsafe_allow_html=True)
    recommendations = [
        f"📈 Prioritize investment in <b>{top_genre_by_rev}</b> movies, which show the strongest average returns.",
        "💵 Use historical budget-vs-revenue trends to plan production budgets rather than guessing.",
        "📣 Boost marketing spend for movies with high early popularity, since this often converts to revenue.",
        "🔍 Study successful low-budget movies to identify repeatable, cost-efficient success factors.",
        "⭐ Focus on story and production quality in genres that consistently receive high ratings.",
    ]
    for rec in recommendations:
        st.markdown(f'<div class="rec-box">{rec}</div>', unsafe_allow_html=True)

# ---------------- TAB 2: MOVIE COMPARISON ----------------
with tab_compare:
    st.subheader("Compare Movies Side-by-Side")
    movie_options = sorted(filtered_df["title"].unique())
    default_selection = movie_options[:2] if len(movie_options) >= 2 else movie_options
    chosen = st.multiselect("Select 2-4 movies to compare", options=movie_options, default=default_selection, max_selections=4)

    if len(chosen) < 2:
        st.info("Select at least 2 movies to see a comparison.")
    else:
        comp_df = filtered_df[filtered_df["title"].isin(chosen)].drop_duplicates(subset="title")
        display_cols = ["title", "genre_clean", "budget", "revenue", "profit", "roi", "vote_average", "popularity", "runtime"]
        st.dataframe(
            comp_df[display_cols].rename(columns={
                "title": "Title", "genre_clean": "Genre", "budget": "Budget", "revenue": "Revenue",
                "profit": "Profit", "roi": "ROI (%)", "vote_average": "Rating",
                "popularity": "Popularity", "runtime": "Runtime"
            }).set_index("Title"),
            use_container_width=True,
        )

        metric_choice = st.selectbox("Compare by metric", options=["revenue", "budget", "profit", "roi", "vote_average", "popularity"],
                                      format_func=lambda x: {"revenue": "Revenue", "budget": "Budget", "profit": "Profit",
                                                              "roi": "ROI (%)", "vote_average": "Rating", "popularity": "Popularity"}[x])
        fig = px.bar(comp_df.sort_values(metric_choice, ascending=False), x="title", y=metric_choice, color="title",
                     color_discrete_sequence=color_seq, labels={"title": "", metric_choice: metric_choice.replace("_", " ").title()})
        fig.update_layout(showlegend=False, height=420)
        st.plotly_chart(fig, use_container_width=True)

        radar_metrics = ["budget", "revenue", "popularity", "vote_average", "runtime"]
        radar_df = comp_df.set_index("title")[radar_metrics].copy()
        radar_norm = (radar_df - df[radar_metrics].min()) / (df[radar_metrics].max() - df[radar_metrics].min())
        fig2 = go.Figure()
        for movie in radar_norm.index:
            fig2.add_trace(go.Scatterpolar(r=radar_norm.loc[movie].values, theta=radar_metrics, fill="toself", name=movie))
        fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=450,
                            title="Normalized Profile Comparison (0-1 scale)")
        st.plotly_chart(fig2, use_container_width=True)

# ---------------- TAB 3: GREENLIGHT SIMULATOR ----------------
with tab_sim:
    st.subheader("💡 Greenlight Simulator — Estimate Performance Before You Commit")
    st.caption("Adjust the sliders to model a hypothetical movie and get a data-driven revenue/ROI estimate based on historical patterns for the chosen genre.")

    s1, s2, s3 = st.columns(3)
    with s1:
        sim_genre = st.selectbox("Genre", options=all_genres)
    with s2:
        sim_budget = st.number_input("Planned Budget ($)", min_value=100_000, max_value=int(df["budget"].max()),
                                      value=50_000_000, step=1_000_000)
    with s3:
        sim_runtime = st.slider("Planned Runtime (minutes)", min_value=runtime_min, max_value=runtime_max,
                                 value=int(df["runtime"].median()))

    genre_df = df[df["genre_clean"] == sim_genre]

    if len(genre_df) >= 5 and genre_df["budget"].std() > 0:
        # Simple linear regression: revenue ~ budget, fit within genre
        coeffs = np.polyfit(genre_df["budget"], genre_df["revenue"], 1)
        predicted_revenue = max(coeffs[0] * sim_budget + coeffs[1], 0)
    else:
        predicted_revenue = genre_df["revenue"].mean() if len(genre_df) > 0 else df["revenue"].mean()

    predicted_profit = predicted_revenue - sim_budget
    predicted_roi = (predicted_profit / sim_budget) * 100 if sim_budget > 0 else 0
    genre_success_rate = genre_df["profitable"].mean() * 100 if len(genre_df) > 0 else 0

    r1, r2, r3 = st.columns(3)
    r1.metric("Predicted Revenue", fmt_money(predicted_revenue))
    r2.metric("Predicted Profit", fmt_money(predicted_profit), delta=f"{predicted_roi:.1f}% ROI")
    r3.metric(f"{sim_genre} Historical Success Rate", f"{genre_success_rate:.1f}%")

    if predicted_roi >= 50:
        st.markdown('<div class="greenlight-box" style="background:linear-gradient(135deg,#6BCB77,#4DCCBD);">✅ GREENLIGHT — Strong projected returns for this genre/budget combination</div>', unsafe_allow_html=True)
    elif predicted_roi >= 0:
        st.markdown('<div class="greenlight-box" style="background:linear-gradient(135deg,#FFD93D,#FF8C42);">⚠️ PROCEED WITH CAUTION — Modest projected returns, consider trimming budget or boosting marketing</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="greenlight-box" style="background:linear-gradient(135deg,#FF4B4B,#FF8C42);">🛑 HIGH RISK — Historical data suggests this budget/genre combination often loses money</div>', unsafe_allow_html=True)

    st.subheader(f"Historical Budget vs Revenue — {sim_genre}")
    fig = px.scatter(genre_df, x="budget", y="revenue", hover_name="title", opacity=0.6,
                      labels={"budget": "Budget ($)", "revenue": "Revenue ($)"}, color_discrete_sequence=["#4D96FF"])
    fig.add_trace(go.Scatter(x=[sim_budget], y=[predicted_revenue], mode="markers",
                              marker=dict(size=16, color="#FF4B4B", symbol="star"), name="Your Simulation"))
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 4: GENRE & RUNTIME INSIGHTS ----------------
with tab_genre:
    st.subheader("Genre Performance")
    c1, c2 = st.columns(2)
    with c1:
        genre_stats = filtered_df.groupby("genre_clean").agg(
            avg_revenue=("revenue", "mean"), avg_roi=("roi", "mean"), count=("title", "count")
        ).reset_index().sort_values("avg_roi", ascending=False)
        fig = px.bar(genre_stats, x="genre_clean", y="avg_roi", color="avg_roi", color_continuous_scale="RdYlGn",
                     labels={"genre_clean": "Genre", "avg_roi": "Avg ROI (%)"})
        fig.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Average ROI (%) by genre")

    with c2:
        genre_count = filtered_df["genre_clean"].value_counts().reset_index()
        genre_count.columns = ["genre_clean", "count"]
        fig = px.pie(genre_count, names="genre_clean", values="count", hole=0.4, color_discrete_sequence=color_seq)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Share of movies by genre")

    st.subheader("Runtime, Rating & Budget Distributions by Genre")
    st.caption("Box plots show the median, typical range, and outliers — clearer than a raw histogram for comparing genres.")
    d1, d2, d3 = st.columns(3)
    with d1:
        fig = px.box(filtered_df, x="genre_clean", y="runtime", color="genre_clean", color_discrete_sequence=color_seq,
                     labels={"genre_clean": "", "runtime": "Runtime (min)"}, points=False)
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
    with d2:
        fig = px.box(filtered_df, x="genre_clean", y="vote_average", color="genre_clean", color_discrete_sequence=color_seq,
                     labels={"genre_clean": "", "vote_average": "Rating"}, points=False)
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)
    with d3:
        fig = px.box(filtered_df, x="genre_clean", y="budget", color="genre_clean", color_discrete_sequence=color_seq,
                     labels={"genre_clean": "", "budget": "Budget ($)"}, points=False)
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Runtime vs Rating")
    fig = px.scatter(filtered_df, x="runtime", y="vote_average", color="genre_clean", size="revenue",
                      hover_name="title", color_discrete_sequence=color_seq,
                      labels={"runtime": "Runtime (min)", "vote_average": "Rating", "genre_clean": "Genre"})
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 5: SMART DATA EXPLORER ----------------
with tab_explore:
    st.subheader("📁 Interactive Data Grid")
    all_cols = ["title", "genre_clean", "budget", "revenue", "profit", "roi", "vote_average", "popularity", "runtime", "budget_category"]
    default_cols = ["title", "genre_clean", "budget", "revenue", "profit", "roi", "vote_average", "popularity"]
    visible_cols = st.multiselect("Select Visible Columns", options=all_cols, default=default_cols)

    if not visible_cols:
        st.info("Select at least one column to display.")
    else:
        display_df = filtered_df[visible_cols].rename(columns={
            "title": "title", "genre_clean": "genre_clean", "budget": "budget", "revenue": "revenue",
            "profit": "profit", "roi": "roi", "vote_average": "vote_average", "popularity": "popularity",
            "runtime": "runtime", "budget_category": "budget_category"
        })
        st.dataframe(display_df, use_container_width=True, height=420)

        st.download_button(
            "📥 Download Current Slice as CSV",
            data=display_df.to_csv(index=False).encode("utf-8"),
            file_name="movie_iq_filtered_data.csv",
            mime="text/csv",
        )

# ----------------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#9AA0A6;'>Movie IQ — Film Analytics Dashboard • Built with Streamlit & Plotly</p>",
    unsafe_allow_html=True,
)
