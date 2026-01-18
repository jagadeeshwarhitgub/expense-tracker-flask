from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            note TEXT,
            date TEXT,
            user_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

create_tables()

# ---------- PRO UI TEMPLATES ----------

base_style = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body { background:#f4f6f9; }
.card { border-radius:15px; }
</style>
"""

login_template = base_style + """
<div class="container mt-5">
  <div class="row justify-content-center">
    <div class="col-md-4">
      <div class="card p-4 shadow">
        <h3 class="text-center mb-3">Expense Tracker Login</h3>
        <form method="POST">
          <input class="form-control mb-2" name="username" placeholder="Username" required>
          <input class="form-control mb-3" type="password" name="password" placeholder="Password" required>
          <button class="btn btn-primary w-100">Login</button>
        </form>
        <p class="text-center mt-3">New user? <a href="/register">Register</a></p>
        <p class="text-danger text-center">{{msg}}</p>
      </div>
    </div>
  </div>
</div>
"""

register_template = base_style + """
<div class="container mt-5">
  <div class="row justify-content-center">
    <div class="col-md-4">
      <div class="card p-4 shadow">
        <h3 class="text-center mb-3">Create Account</h3>
        <form method="POST">
          <input class="form-control mb-2" name="username" placeholder="Username" required>
          <input class="form-control mb-3" type="password" name="password" placeholder="Password" required>
          <button class="btn btn-success w-100">Register</button>
        </form>
        <p class="text-center mt-3"><a href="/">Back to Login</a></p>
        <p class="text-danger text-center">{{msg}}</p>
      </div>
    </div>
  </div>
</div>
"""

dashboard_template = base_style + """
<nav class="navbar navbar-dark bg-dark px-4">
  <span class="navbar-brand">Expense Tracker</span>
  <a class="btn btn-sm btn-light" href="/logout">Logout</a>
</nav>

<div class="container mt-4">

  <div class="card p-3 mb-4 shadow">
    <h4>Total Expense: ₹ {{total}}</h4>
  </div>

  <div class="card p-4 shadow mb-4">
    <h5>Add Expense</h5>
    <form method="POST" action="/add" class="row g-2">
      <div class="col-md-3">
        <input class="form-control" name="amount" placeholder="Amount" required>
      </div>
      <div class="col-md-3">
        <input class="form-control" name="category" placeholder="Category" required>
      </div>
      <div class="col-md-4">
        <input class="form-control" name="note" placeholder="Note">
      </div>
      <div class="col-md-2">
        <button class="btn btn-primary w-100">Add</button>
      </div>
    </form>
  </div>

  <div class="card p-3 shadow">
    <h5>Your Expenses</h5>
    <table class="table table-striped mt-2">
      <tr>
        <th>Amount</th>
        <th>Category</th>
        <th>Note</th>
        <th>Date</th>
        <th></th>
      </tr>
      {% for e in expenses %}
      <tr>
        <td>₹ {{e.amount}}</td>
        <td>{{e.category}}</td>
        <td>{{e.note}}</td>
        <td>{{e.date}}</td>
        <td>
          <a class="btn btn-sm btn-danger" href="/delete/{{e.id}}">Delete</a>
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>

</div>
"""

# ---------- ROUTES ----------

@app.route("/", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u, p)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        else:
            msg = "Invalid login"

    return render_template_string(login_template, msg=msg)

@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        try:
            conn = get_db()
            conn.execute("INSERT INTO users(username,password) VALUES (?,?)", (u, p))
            conn.commit()
            conn.close()
            return redirect("/")
        except:
            msg = "Username already exists"

    return render_template_string(register_template, msg=msg)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    expenses = conn.execute(
        "SELECT * FROM expenses WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    total = conn.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()[0]

    conn.close()
    return render_template_string(dashboard_template, expenses=expenses, total=total or 0)

@app.route("/add", methods=["POST"])
def add_expense():
    if "user_id" not in session:
        return redirect("/")

    amount = request.form["amount"]
    category = request.form["category"]
    note = request.form["note"]
    date = datetime.now().strftime("%d-%m-%Y")

    conn = get_db()
    conn.execute(
        "INSERT INTO expenses(amount,category,note,date,user_id) VALUES (?,?,?,?,?)",
        (amount, category, note, date, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
