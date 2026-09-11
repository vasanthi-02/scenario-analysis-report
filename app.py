from flask import Flask, render_template_string, request, redirect, session, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import sqlite3
import os
import tempfile

app = Flask(__name__)
app.secret_key = "scenario_report_secret_key"

DB_NAME = os.path.join(tempfile.gettempdir(), "database.db")

# ---------------------------------------------------------------------------
# CSS (was static/style.css) — inlined so nothing external needs bundling
# ---------------------------------------------------------------------------
STYLE_CSS = """
body {
    font-family: Arial, sans-serif;
    background-color: #f4f6f8;
    margin: 0;
    color: #222;
}
.top-bar {
    background-color: #1f3b57;
    color: white;
    padding: 15px 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.top-bar a {
    color: white;
    text-decoration: none;
    font-weight: bold;
}
.container {
    max-width: 900px;
    margin: 25px auto;
    background: white;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 0 8px rgba(0,0,0,0.1);
}
.form-box {
    max-width: 350px;
    margin: 80px auto;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 0 8px rgba(0,0,0,0.1);
    text-align: center;
}
.form-box h2 {
    color: #1f3b57;
}
label {
    display: block;
    margin-top: 12px;
    margin-bottom: 4px;
    font-weight: bold;
    text-align: left;
}
input {
    width: 100%;
    padding: 8px;
    box-sizing: border-box;
    border: 1px solid #ccc;
    border-radius: 4px;
}
button {
    background-color: #1f3b57;
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 15px;
}
button:hover {
    background-color: #163049;
}
.btn {
    background-color: #1f3b57;
    color: white;
    padding: 8px 14px;
    border-radius: 4px;
    text-decoration: none;
}
.link-btn {
    background: none;
    border: none;
    color: #c0392b;
    cursor: pointer;
    padding: 0;
    margin: 0;
    text-decoration: underline;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
table th, table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
table th {
    background-color: #eaf0f5;
}
.stage-row {
    background-color: #fafafa;
    padding: 10px;
    border-radius: 6px;
    margin-top: 10px;
}
.summary-box {
    margin-top: 20px;
    padding: 15px;
    background-color: #eaf6ec;
    border-left: 4px solid #2e7d32;
    border-radius: 4px;
}
.hint {
    color: #666;
    font-size: 14px;
}
.error {
    color: #c0392b;
    font-weight: bold;
}
"""


@app.route("/static/style.css")
def style_css():
    return Response(STYLE_CSS, mimetype="text/css")


# ---------------------------------------------------------------------------
# Templates (were templates/*.html) — inlined as strings, rendered with
# render_template_string so Jinja syntax (url_for, loops, filters) still works
# ---------------------------------------------------------------------------

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Scenario Report</title>
    <link rel="stylesheet" href="{{ url_for('style_css') }}">
</head>
<body>
    <div class="form-box">
        <h2>Advisor Login</h2>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <label>Username</label>
            <input type="text" name="username" required>
            <label>Password</label>
            <input type="password" name="password" required>
            <button type="submit">Login</button>
        </form>
        <p>New advisor? <a href="{{ url_for('register') }}">Register here</a></p>
    </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Register - Scenario Report</title>
    <link rel="stylesheet" href="{{ url_for('style_css') }}">
</head>
<body>
    <div class="form-box">
        <h2>Advisor Registration</h2>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <label>Username</label>
            <input type="text" name="username" required>
            <label>Password</label>
            <input type="password" name="password" required>
            <button type="submit">Register</button>
        </form>
        <p>Already have an account? <a href="{{ url_for('login') }}">Login here</a></p>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Scenario Report</title>
    <link rel="stylesheet" href="{{ url_for('style_css') }}">
</head>
<body>
    <div class="top-bar">
        <h2>Welcome, {{ username }}</h2>
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>

    <div class="container">
        <div class="top-bar">
            <h3>Your Scenario Reports</h3>
            <a class="btn" href="{{ url_for('new_report') }}">+ New Report</a>
        </div>

        {% if reports|length == 0 %}
            <p>No reports created yet. Click "New Report" to create your first one.</p>
        {% else %}
            <table>
                <tr>
                    <th>Client Name</th>
                    <th>Created On</th>
                    <th>Action</th>
                </tr>
                {% for report in reports %}
                <tr>
                    <td>{{ report["client_name"] }}</td>
                    <td>{{ report["created_at"] }}</td>
                    <td>
                        <a href="{{ url_for('view_report', report_id=report['id']) }}">View</a>
                        &nbsp;|&nbsp;
                        <form action="{{ url_for('delete_report', report_id=report['id']) }}" method="POST" style="display:inline">
                            <button type="submit" class="link-btn" onclick="return confirm('Delete this report?')">Delete</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        {% endif %}
    </div>
</body>
</html>
"""

NEW_REPORT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>New Report - Scenario Report</title>
    <link rel="stylesheet" href="{{ url_for('style_css') }}">
</head>
<body>
    <div class="top-bar">
        <h2>Create Scenario Analysis Report</h2>
        <a href="{{ url_for('dashboard') }}">Back to Dashboard</a>
    </div>

    <div class="container">
        <form action="{{ url_for('create_report') }}" method="POST">
            <label>Client Name</label>
            <input type="text" name="client_name" required>

            <h3>Advice Stages</h3>
            <p class="hint">Add each point in time where you gave investment advice to the client.</p>

            <div id="stages-container">
                <div class="stage-row">
                    <label>Stage Date</label>
                    <input type="date" name="stage_date[]" required>

                    <label>Amount Invested (₹)</label>
                    <input type="number" step="0.01" name="amount[]" required>

                    <label>Advised Annual Return (%)</label>
                    <input type="number" step="0.01" name="advised_return[]" required>

                    <label>Advice Given</label>
                    <input type="text" name="advice_text[]" placeholder="e.g. Invest in Nifty 50 index fund" required>
                    <hr>
                </div>
            </div>

            <button type="button" onclick="addStage()">+ Add Another Stage</button>
            <br><br>
            <button type="submit">Generate Report</button>
        </form>
    </div>

    <script>
        function addStage() {
            const container = document.getElementById("stages-container");
            const firstRow = container.querySelector(".stage-row");
            const newRow = firstRow.cloneNode(true);
            const inputs = newRow.querySelectorAll("input");
            inputs.forEach(function (input) {
                input.value = "";
            });
            container.appendChild(newRow);
        }
    </script>
</body>
</html>
"""

VIEW_REPORT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Report - {{ report["client_name"] }}</title>
    <link rel="stylesheet" href="{{ url_for('style_css') }}">
</head>
<body>
    <div class="top-bar">
        <h2>Scenario Analysis Report</h2>
        <a href="{{ url_for('dashboard') }}">Back to Dashboard</a>
    </div>

    <div class="container">
        <p><strong>Client Name:</strong> {{ report["client_name"] }}</p>
        <p><strong>Report Generated On:</strong> {{ report["created_at"] }}</p>

        <h3>Advice Given at Each Stage</h3>
        <table>
            <tr>
                <th>Stage Date</th>
                <th>Amount Invested (₹)</th>
                <th>Advised Return (%)</th>
                <th>Advice</th>
                <th>Years Since Stage</th>
                <th>Value If Advice Followed (₹)</th>
            </tr>
            {% for stage in stages %}
            <tr>
                <td>{{ stage["stage_date"] }}</td>
                <td>{{ "%.2f"|format(stage["amount"]) }}</td>
                <td>{{ stage["advised_return"] }}</td>
                <td>{{ stage["advice_text"] }}</td>
                <td>{{ "%.2f"|format(stage["years"]) }}</td>
                <td>{{ "%.2f"|format(stage["future_value"]) }}</td>
            </tr>
            {% endfor %}
        </table>

        <div class="summary-box">
            <p><strong>Total Amount Invested:</strong> ₹{{ "%.2f"|format(total_invested) }}</p>
            <p><strong>Total Present Value If Advice Was Followed:</strong> ₹{{ "%.2f"|format(total_value) }}</p>
            <p><strong>Growth From Advice:</strong> ₹{{ "%.2f"|format(total_value - total_invested) }}</p>
        </div>

        <p class="hint">
            This report shows what the client's portfolio would be worth today if they had followed the advisor's
            recommendations at each stage, assuming the advised annual return was achieved.
        </p>
    </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

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
    return render_template_string(REGISTER_HTML, error=error)


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
    return render_template_string(LOGIN_HTML, error=error)


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
    return render_template_string(DASHBOARD_HTML, reports=reports, username=session["username"])


@app.route("/new_report")
def new_report():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template_string(NEW_REPORT_HTML)


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
    return render_template_string(
        VIEW_REPORT_HTML, report=report, stages=stages,
        total_value=total_value, total_invested=total_invested
    )


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
