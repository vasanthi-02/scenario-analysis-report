from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "scenario_report_secret_key"

if os.environ.get("VERCEL"):
    DB_NAME = "/tmp/database.db"
else:
    DB_NAME = "database.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            stage_date TEXT NOT NULL,
            amount REAL NOT NULL,
            advised_return REAL NOT NULL,
            advice_text TEXT NOT NULL,
            years REAL NOT NULL,
            future_value REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def calculate_future_value(amount, advised_return, stage_date_str):
    stage_date = datetime.strptime(stage_date_str, "%Y-%m-%d").date()
    today = date.today()
    days_diff = (today - stage_date).days
    years = days_diff / 365.25
    future_value = amount * ((1 + advised_return / 100) ** years)
    return years, future_value


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cur.fetchone()
        if existing:
            error = "Username already taken"
        else:
            hashed_password = generate_password_hash(password)
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        conn.close()
    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reports WHERE user_id = ? ORDER BY id DESC", (session["user_id"],))
    reports = cur.fetchall()
    conn.close()
    return render_template("dashboard.html", reports=reports, username=session["username"])


@app.route("/new_report")
def new_report():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("new_report.html")


@app.route("/create_report", methods=["POST"])
def create_report():
    if "user_id" not in session:
        return redirect(url_for("login"))

    client_name = request.form["client_name"]
    stage_dates = request.form.getlist("stage_date[]")
    amounts = request.form.getlist("amount[]")
    advised_returns = request.form.getlist("advised_return[]")
    advice_texts = request.form.getlist("advice_text[]")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reports (user_id, client_name, created_at) VALUES (?, ?, ?)",
        (session["user_id"], client_name, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    report_id = cur.lastrowid

    for i in range(len(stage_dates)):
        amount = float(amounts[i])
        advised_return = float(advised_returns[i])
        years, future_value = calculate_future_value(amount, advised_return, stage_dates[i])
        cur.execute("""
            INSERT INTO stages (report_id, stage_date, amount, advised_return, advice_text, years, future_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (report_id, stage_dates[i], amount, advised_return, advice_texts[i], years, future_value))

    conn.commit()
    conn.close()
    return redirect(url_for("view_report", report_id=report_id))


@app.route("/report/<int:report_id>")
def view_report(report_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reports WHERE id = ? AND user_id = ?", (report_id, session["user_id"]))
    report = cur.fetchone()
    if not report:
        conn.close()
        return redirect(url_for("dashboard"))
    cur.execute("SELECT * FROM stages WHERE report_id = ? ORDER BY stage_date ASC", (report_id,))
    stages = cur.fetchall()
    conn.close()
    total_value = sum(stage["future_value"] for stage in stages)
    total_invested = sum(stage["amount"] for stage in stages)
    return render_template("view_report.html", report=report, stages=stages, total_value=total_value, total_invested=total_invested)


@app.route("/delete_report/<int:report_id>", methods=["POST"])
def delete_report(report_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM reports WHERE id = ? AND user_id = ?", (report_id, session["user_id"]))
    cur.execute("DELETE FROM stages WHERE report_id = ?", (report_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
