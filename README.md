# Scenario Analysis Report

A simple web app that lets a financial advisor generate a scenario analysis report for a client. The report shows what the client's investment would be worth today if they had followed the advisor's advice at different points in time.

## What it does

A financial advisor logs in and creates a report for a client. For each report, the advisor adds one or more "advice stages" — a point in time where they recommended the client invest a certain amount at an expected annual return. The app then calculates, using compound interest, what that money would be worth today if the advice had actually been followed.

## Tech Stack

- Python (Flask) for the backend
- SQLite for the database
- HTML, CSS, and plain JavaScript for the frontend (Flask templates, no separate frontend framework)

## Features

- Advisor registration and login (passwords are hashed, not stored in plain text)
- Create a report with multiple advice stages for a client
- Automatic calculation of present value using compound interest
- View all past reports on a dashboard
- Delete old reports

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
├── app.py
├── requirements.txt
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── new_report.html
│   └── view_report.html
└── static/
    └── style.css
```

## How to Run

1. Clone this repository:
   ```
   git clone https://github.com/YOUR-USERNAME/scenario-analysis-report.git
   cd scenario-analysis-report
   ```

2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the app:
   ```
   python app.py
   ```

4. Open your browser and go to:
   ```
   http://127.0.0.1:5000/
   ```

5. Register an advisor account, log in, and click "New Report" to create your first scenario analysis report.

The database file (`database.db`) is created automatically the first time you run the app.

## Limitations (MVP scope)

- Assumes the advised return rate was achieved exactly every year — does not use real market data
- Does not compare against what the client's portfolio would actually be worth if the advice was not followed (no baseline/actual value comparison)
- Single advisor accounts only, no roles or admin features
- Not meant for production use as-is (uses Flask's development server)
