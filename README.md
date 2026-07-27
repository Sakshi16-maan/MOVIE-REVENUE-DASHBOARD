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
- **Sidebar filters**: genre, budget category, box office outcome (profitable/flop),
  runtime range, and a title search box
- **Colorful KPI cards**: selected movies, avg budget, avg revenue, success rate, avg ROI
- **Five tabs**:
  - **Executive Overview** — Top 10 Revenue Movies, Budget vs Revenue, Avg Revenue by
    Genre, Profitable vs Loss pie, plus auto-generated Business Insights & Recommendations
  - **Movie Comparison** — pick 2-4 movies and compare them via table, bar chart, and
    a normalized radar chart
  - **Greenlight Simulator** — set a hypothetical budget/genre/runtime and get a
    regression-based revenue/ROI prediction with a greenlight/caution/high-risk verdict
  - **Genre & Runtime Insights** — ROI by genre, genre share, and box plots (not raw
    histograms) for runtime, rating, and budget by genre — clearer for comparing spread
    and outliers across genres
  - **Smart Data Explorer** — pick which columns to view, then download the filtered
    slice as CSV
- The app auto-detects the CSV file even if it gets renamed (e.g. `movies (3).csv`),
  so a filename mismatch won't break deployment again

## Data cleaning performed
- Trimmed whitespace from text fields
- Removed duplicate rows
- Converted numeric columns to proper numeric dtypes
- Filled any missing numeric values with the median (none were present in this dataset)
- Removed rows with negative budget/revenue (none were present in this dataset)
- Parsed the `genres` column (stored as a stringified list of dicts, e.g.
  `[{'id': 18, 'name': 'Drama'}]`) into a clean `primary_genre` column
