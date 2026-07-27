# 🎬 Movie Revenue Analysis Dashboard

An interactive Streamlit dashboard that analyzes movie data (budget, revenue,
popularity, runtime, ratings, genres) to help production companies make
data-driven decisions.

## Files
- `app.py` — the Streamlit application
- `movies.csv` — the dataset (must stay in the same folder as `app.py`)
- `requirements.txt` — Python dependencies

## How to run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure `movies.csv` is in the same folder as `app.py`.

3. Launch the app:
   ```bash
   streamlit run app.py
   ```

4. Your browser will open at `http://localhost:8501`.

## Features
- **Sidebar filters**: genre, budget range, rating range, runtime range
- **Colorful KPI cards**: total movies, average revenue, average budget,
  average rating, average popularity
- **Dataset preview** with CSV download of the filtered data
- **Interactive charts** (Plotly), organized into tabs:
  - Revenue Insights: Top 10 Revenue Movies, Budget vs Revenue, Popularity vs Revenue
  - Genre & Ratings: Avg Revenue by Genre, Genre Share, Rating Distribution
  - Distributions: Runtime Distribution, Budget Distribution
- **Business Insights** — auto-generated from the filtered data (top genre,
  budget/revenue correlation, popularity/revenue correlation, etc.)
- **Business Recommendations** — actionable suggestions for producers

## Data cleaning performed
- Trimmed whitespace from text fields
- Removed duplicate rows
- Converted numeric columns to proper numeric dtypes
- Filled any missing numeric values with the median (none were present in this dataset)
- Removed rows with negative budget/revenue (none were present in this dataset)
- Parsed the `genres` column (stored as a stringified list of dicts, e.g.
  `[{'id': 18, 'name': 'Drama'}]`) into a clean `primary_genre` column
