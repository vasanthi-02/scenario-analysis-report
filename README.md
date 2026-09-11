# Scenario Analysis Report

A simple web app that lets a financial advisor generate a scenario analysis report for a client. The report shows what the client's investment would be worth today if they had followed the advisor's advice at different points in time.

**Live app:** https://scenario-analysis-report.vercel.app

## What it does

A financial advisor logs in and creates a report for a client. For each report, the advisor adds one or more "advice stages" — a point in time where they recommended the client invest a certain amount at an expected annual return. The app then calculates, using compound interest, what that money would be worth today if the advice had actually been followed.

## Tech Stack

- Python (Flask) for the backend
- PostgreSQL (hosted on [Neon](https://neon.tech)) for the database
- HTML, CSS, and plain JavaScript for the frontend — all templates and styles are inlined directly in `app.py` (no separate `templates/` or `static/` folders), which keeps the app to a single deployable file and avoids file-bundling issues on serverless platforms
- Hosted on [Vercel](https://vercel.com)

## Features

- Advisor registration and login (passwords are hashed, not stored in plain text)
- Create a report with multiple advice stages for a client
- Automatic calculation of present value using compound interest
- View all past reports on a dashboard
- Delete old reports
- Data persists reliably across visits (backed by Postgres, not local/ephemeral storage)

## How the calculation works

For every stage entered by the advisor:

```
years = (today's date - stage date) in years
future_value = amount_invested * (1 + advised_return / 100) ^ years
```

All stage values are added up to get the total present value if the advice was followed.

## Project Structure

```
scenario_report/
├── app.py             # entire app: routes, DB logic, HTML templates, and CSS
└── requirements.txt
```

All HTML pages and CSS live inside `app.py` as strings, rendered with Flask's `render_template_string`. There is no separate `templates/` or `static/` folder.

## How to Run Locally

1. Clone this repository:
   ```
   git clone https://github.com/YOUR-USERNAME/scenario-analysis-report.git
   cd scenario-analysis-report
   ```

2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up a Postgres database and set the `DATABASE_URL` environment variable. The easiest way is a free [Neon](https://neon.tech) project — copy its connection string and set:
   ```
   export DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
   ```
   (On Windows: `set DATABASE_URL=...`)

4. Run the app:
   ```
   python app.py
   ```

5. Open your browser and go to:
   ```
   http://127.0.0.1:5000/
   ```

6. Register an advisor account, log in, and click "New Report" to create your first scenario analysis report.

The required tables (`users`, `reports`, `stages`) are created automatically the first time the app starts.

## Deployment

The live version is deployed on Vercel, with `DATABASE_URL` set as a project environment variable pointing to a Neon Postgres instance. No other configuration is needed — Vercel auto-detects the Flask app from `app.py`.

## Limitations (MVP scope)

- Assumes the advised return rate was achieved exactly every year — does not use real market data
- Does not compare against what the client's portfolio would actually be worth if the advice was not followed (no baseline/actual value comparison)
- Single advisor accounts only, no roles or admin features
- Not meant for high-traffic production use as-is (single Flask app, no caching or rate limiting)
