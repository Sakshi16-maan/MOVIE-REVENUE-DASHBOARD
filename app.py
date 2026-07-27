import ast
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Movie Revenue Analysis Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# CUSTOM CSS - for colorful KPI cards & overall styling
# ----------------------------------------------------------------------------
st.markdown("""
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #FF4B4B, #FF8C42, #FFD93D, #6BCB77, #4D96FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding-bottom: 0px;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #9AA0A6;
        font-size: 18px;
        margin-top: 0px;
        margin-bottom: 20px;
    }
    .kpi-card {
        border-radius: 16px;
        padding: 20px 15px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin-bottom: 10px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        margin: 0px;
    }
    .kpi-label {
        font-size: 14px;
        font-weight: 500;
        opacity: 0.9;
        margin: 0px;
    }
    .section-header {
        font-size: 26px;
        font-weight: 700;
        margin-top: 30px;
        margin-bottom: 10px;
        border-left: 6px solid #FF4B4B;
        padding-left: 12px;
    }
    .insight-box {
        background-color: rgba(107, 203, 119, 0.12);
        border-left: 5px solid #6BCB77;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 16px;
    }
    .rec-box {
        background-color: rgba(77, 150, 255, 0.12);
        border-left: 5px solid #4D96FF;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# DATA LOADING & CLEANING
# ----------------------------------------------------------------------------
@st.cache_data
def load_data(path="movies.csv"):
    df = pd.read_csv(path)

    # Remove unnecessary spaces from column names & string columns
    df.columns = [c.strip() for c in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    # Drop exact duplicate rows
    df = df.drop_duplicates()

    # Fix data types
    numeric_cols = ["budget", "revenue", "popularity", "runtime", "vote_average"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Handle missing values (median for numeric, mode/"Unknown" for text)
    for col in numeric_cols:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())
    if df["title"].isnull().sum() > 0:
        df["title"] = df["title"].fillna("Unknown")
    if df["genres"].isnull().sum() > 0:
        df["genres"] = df["genres"].fillna("Unknown")

    # Remove rows with negative budget/revenue (data errors)
    df = df[(df["budget"] >= 0) & (df["revenue"] >= 0)]

    # Parse genres column: stored as stringified list of dicts -> extract genre name(s)
    def extract_genre(g):
        try:
            parsed = ast.literal_eval(g)
            if isinstance(parsed, list) and len(parsed) > 0:
                names = [d.get("name", "Unknown") for d in parsed if isinstance(d, dict)]
                return ", ".join(names) if names else "Unknown"
            return "Unknown"
        except (ValueError, SyntaxError):
            return "Unknown"

    df["genre_list"] = df["genres"].apply(extract_genre)
    df["primary_genre"] = df["genre_list"].apply(lambda x: x.split(",")[0].strip() if x else "Unknown")

    df = df.reset_index(drop=True)
    return df


df = load_data()

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown('<p class="main-title">🎬 Movie Revenue Analysis Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Helping producers decide what makes a movie successful</p>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------------------------------
st.sidebar.header("🔍 Filters")

all_genres = sorted(df["primary_genre"].unique())
selected_genres = st.sidebar.multiselect("Select Genre(s)", options=all_genres, default=all_genres)

budget_min, budget_max = int(df["budget"].min()), int(df["budget"].max())
selected_budget = st.sidebar.slider(
    "Budget Range ($)", min_value=budget_min, max_value=budget_max,
    value=(budget_min, budget_max), step=max(1, (budget_max - budget_min) // 100)
)

rating_min, rating_max = float(df["vote_average"].min()), float(df["vote_average"].max())
selected_rating = st.sidebar.slider(
    "Rating Range", min_value=round(rating_min, 1), max_value=round(rating_max, 1),
    value=(round(rating_min, 1), round(rating_max, 1)), step=0.1
)

runtime_min, runtime_max = int(df["runtime"].min()), int(df["runtime"].max())
selected_runtime = st.sidebar.slider(
    "Runtime (minutes)", min_value=runtime_min, max_value=runtime_max,
    value=(runtime_min, runtime_max)
)

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ using Streamlit")

# Apply filters
filtered_df = df[
    (df["primary_genre"].isin(selected_genres)) &
    (df["budget"].between(selected_budget[0], selected_budget[1])) &
    (df["vote_average"].between(selected_rating[0], selected_rating[1])) &
    (df["runtime"].between(selected_runtime[0], selected_runtime[1]))
]

if filtered_df.empty:
    st.warning("⚠️ No movies match the selected filters. Please adjust your filter selection.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI CARDS
# ----------------------------------------------------------------------------
st.markdown('<p class="section-header">📊 Key Performance Indicators</p>', unsafe_allow_html=True)

total_movies = len(filtered_df)
avg_revenue = filtered_df["revenue"].mean()
avg_budget = filtered_df["budget"].mean()
avg_rating = filtered_df["vote_average"].mean()
avg_popularity = filtered_df["popularity"].mean()

def fmt_money(x):
    if x >= 1e9:
        return f"${x/1e9:.2f}B"
    elif x >= 1e6:
        return f"${x/1e6:.2f}M"
    elif x >= 1e3:
        return f"${x/1e3:.1f}K"
    return f"${x:.0f}"

kpi_data = [
    ("🎞️ Total Movies", f"{total_movies:,}", "linear-gradient(135deg,#FF4B4B,#FF8C42)"),
    ("💰 Avg Revenue", fmt_money(avg_revenue), "linear-gradient(135deg,#4D96FF,#4DCCBD)"),
    ("💵 Avg Budget", fmt_money(avg_budget), "linear-gradient(135deg,#6BCB77,#4D96FF)"),
    ("⭐ Avg Rating", f"{avg_rating:.2f}/10", "linear-gradient(135deg,#FFD93D,#FF8C42)"),
    ("🔥 Avg Popularity", f"{avg_popularity:.1f}", "linear-gradient(135deg,#B983FF,#FF4B4B)"),
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
# DATASET PREVIEW
# ----------------------------------------------------------------------------
st.markdown('<p class="section-header">📄 Dataset Preview</p>', unsafe_allow_html=True)
with st.expander("Click to view filtered dataset", expanded=False):
    st.dataframe(
        filtered_df[["title", "primary_genre", "budget", "revenue", "popularity", "runtime", "vote_average"]]
        .rename(columns={
            "title": "Title", "primary_genre": "Genre", "budget": "Budget",
            "revenue": "Revenue", "popularity": "Popularity",
            "runtime": "Runtime", "vote_average": "Rating"
        }),
        use_container_width=True,
        height=300,
    )
    st.download_button(
        "⬇️ Download Filtered Data as CSV",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_movies.csv",
        mime="text/csv",
    )

# ----------------------------------------------------------------------------
# CHARTS
# ----------------------------------------------------------------------------
st.markdown('<p class="section-header">📈 Interactive Charts</p>', unsafe_allow_html=True)

color_seq = px.colors.qualitative.Bold

tab1, tab2, tab3 = st.tabs(["💰 Revenue Insights", "🎭 Genre & Ratings", "⏱️ Distributions"])

with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Top 10 Revenue Movies")
        top10 = filtered_df.nlargest(10, "revenue").sort_values("revenue")
        fig = px.bar(
            top10, x="revenue", y="title", orientation="h",
            color="revenue", color_continuous_scale="Sunset",
            labels={"revenue": "Revenue ($)", "title": "Movie"},
        )
        fig.update_layout(showlegend=False, height=420)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Budget vs Revenue")
        fig = px.scatter(
            filtered_df, x="budget", y="revenue", color="primary_genre",
            size="popularity", hover_name="title",
            labels={"budget": "Budget ($)", "revenue": "Revenue ($)", "primary_genre": "Genre"},
            color_discrete_sequence=color_seq,
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Popularity vs Revenue")
    fig = px.scatter(
        filtered_df, x="popularity", y="revenue", color="vote_average",
        size="budget", hover_name="title",
        labels={"popularity": "Popularity", "revenue": "Revenue ($)", "vote_average": "Rating"},
        color_continuous_scale="Viridis",
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Average Revenue by Genre")
        genre_rev = filtered_df.groupby("primary_genre")["revenue"].mean().sort_values(ascending=False).reset_index()
        fig = px.bar(
            genre_rev, x="primary_genre", y="revenue", color="primary_genre",
            labels={"primary_genre": "Genre", "revenue": "Avg Revenue ($)"},
            color_discrete_sequence=color_seq,
        )
        fig.update_layout(showlegend=False, height=420)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Genre Popularity Share")
        genre_count = filtered_df["primary_genre"].value_counts().reset_index()
        genre_count.columns = ["primary_genre", "count"]
        fig = px.pie(
            genre_count, names="primary_genre", values="count",
            color_discrete_sequence=color_seq, hole=0.4,
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Rating Distribution")
    fig = px.histogram(
        filtered_df, x="vote_average", nbins=20, color_discrete_sequence=["#FF8C42"],
        labels={"vote_average": "Rating"},
    )
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Runtime Distribution")
        fig = px.histogram(
            filtered_df, x="runtime", nbins=25, color_discrete_sequence=["#4D96FF"],
            labels={"runtime": "Runtime (minutes)"},
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Budget Distribution")
        fig = px.histogram(
            filtered_df, x="budget", nbins=25, color_discrete_sequence=["#6BCB77"],
            labels={"budget": "Budget ($)"},
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# BUSINESS INSIGHTS
# ----------------------------------------------------------------------------
st.markdown('<p class="section-header">💡 Business Insights</p>', unsafe_allow_html=True)

# Compute a few data-driven insight numbers
top_genre_by_rev = filtered_df.groupby("primary_genre")["revenue"].mean().idxmax()
corr_budget_rev = filtered_df["budget"].corr(filtered_df["revenue"])
corr_pop_rev = filtered_df["popularity"].corr(filtered_df["revenue"])
top_rated_movie = filtered_df.loc[filtered_df["vote_average"].idxmax(), "title"]
highest_revenue_movie = filtered_df.loc[filtered_df["revenue"].idxmax(), "title"]

insights = [
    f"🎬 <b>{highest_revenue_movie}</b> earns the highest revenue among the filtered movies.",
    f"🏆 <b>{top_genre_by_rev}</b> is the genre with the highest average revenue.",
    f"💰 Budget and revenue show a correlation of <b>{corr_budget_rev:.2f}</b> — "
    + ("higher budgets tend to be associated with higher revenue." if corr_budget_rev > 0.3
       else "budget alone is not a strong predictor of revenue."),
    f"🔥 Popularity and revenue show a correlation of <b>{corr_pop_rev:.2f}</b> — "
    + ("more popular movies tend to earn more." if corr_pop_rev > 0.3
       else "popularity alone doesn't guarantee higher revenue."),
    f"⭐ <b>{top_rated_movie}</b> has the highest audience rating in the current selection.",
    "🎯 Some low-budget movies achieve strong revenue, showing that a smart concept can outperform a big budget.",
]

for ins in insights:
    st.markdown(f'<div class="insight-box">{ins}</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# BUSINESS RECOMMENDATIONS
# ----------------------------------------------------------------------------
st.markdown('<p class="section-header">📌 Business Recommendations</p>', unsafe_allow_html=True)

recommendations = [
    f"📈 Prioritize investment in <b>{top_genre_by_rev}</b> movies, which show the strongest average returns.",
    "💵 Use historical budget-vs-revenue trends to plan production budgets rather than guessing.",
    "📣 Boost marketing spend for movies that already show high early popularity, since this often converts to revenue.",
    "🔍 Study successful low-budget movies to identify repeatable, cost-efficient success factors.",
    "⭐ Focus on story and production quality in genres that consistently receive high ratings, as ratings help attract audiences.",
    "🎯 Diversify the movie portfolio across a few well-performing genres instead of over-relying on one.",
]

for rec in recommendations:
    st.markdown(f'<div class="rec-box">{rec}</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#9AA0A6;'>Movie Revenue Analysis Dashboard • Built with Streamlit & Plotly</p>",
    unsafe_allow_html=True,
)
