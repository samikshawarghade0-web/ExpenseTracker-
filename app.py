from flask import Flask, request, redirect, url_for, session, render_template_string, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "expense_tracker_secret_key"

DB_NAME = "expense_tracker.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- CSS ----------------

STYLE = """
<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
}

body {
    background: #f4f1ff;
    color: #222;
}

.navbar {
    background: #6c4ab6;
    color: white;
    padding: 18px 7%;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 25px;
    font-weight: bold;
}

.navbar a {
    color: white;
    text-decoration: none;
    margin-left: 20px;
}

.container {
    width: 90%;
    max-width: 1100px;
    margin: 35px auto;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    margin-bottom: 25px;
}

.auth-box {
    width: 400px;
    max-width: 90%;
    margin: 70px auto;
}

h1, h2, h3 {
    margin-bottom: 18px;
}

input, select, textarea {
    width: 100%;
    padding: 12px;
    margin: 8px 0 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
}

button {
    background: #6c4ab6;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 8px;
    cursor: pointer;
}

button:hover {
    background: #56349c;
}

.link {
    color: #6c4ab6;
    text-decoration: none;
    font-weight: bold;
}

.cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 25px;
}

.stat {
    background: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
}

.stat h3 {
    color: #777;
}

.amount {
    font-size: 28px;
    font-weight: bold;
}

.income {
    color: green;
}

.expense {
    color: red;
}

.balance {
    color: #6c4ab6;
}

.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
}

.full {
    grid-column: 1 / -1;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 12px;
    border-bottom: 1px solid #eee;
    text-align: left;
}

th {
    background: #f5f2ff;
}

.delete-btn {
    background: #e74c3c;
    padding: 7px 12px;
}

.alert {
    padding: 12px;
    margin-bottom: 15px;
    border-radius: 8px;
    background: #fff0f0;
    color: #c0392b;
}

@media(max-width: 700px) {

    .cards {
        grid-template-columns: 1fr;
    }

    .form-grid {
        grid-template-columns: 1fr;
    }

    table {
        font-size: 13px;
    }

    .navbar {
        flex-direction: column;
        gap: 10px;
    }
}

</style>
"""


# ---------------- LOGIN PAGE ----------------

LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ExpenseTracker - Login</title>
""" + STYLE + """
</head>

<body>

<div class="auth-box">

    <div class="card">

        <h1>💰 ExpenseTracker</h1>

        <p style="margin-bottom:20px;">
            Login to manage your expenses
        </p>

        {% with messages = get_flashed_messages() %}
            {% for message in messages %}
                <div class="alert">{{ message }}</div>
            {% endfor %}
        {% endwith %}

        <form method="POST">

            <label>Email</label>
            <input type="email" name="email" placeholder="Enter your email" required>

            <label>Password</label>
            <input type="password" name="password" placeholder="Enter your password" required>

            <button type="submit" style="width:100%;">
                Login
            </button>

        </form>

        <p style="margin-top:20px;">
            Don't have an account?
            <a class="link" href="{{ url_for('signup') }}">Sign Up</a>
        </p>

    </div>

</div>

</body>
</html>
"""


# ---------------- SIGNUP PAGE ----------------

SIGNUP_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ExpenseTracker - Sign Up</title>
""" + STYLE + """
</head>

<body>

<div class="auth-box">

    <div class="card">

        <h1>💰 ExpenseTracker</h1>

        <p style="margin-bottom:20px;">
            Create your account
        </p>

        {% with messages = get_flashed_messages() %}
            {% for message in messages %}
                <div class="alert">{{ message }}</div>
            {% endfor %}
        {% endwith %}

        <form method="POST">

            <label>Name</label>
            <input type="text" name="name" placeholder="Enter your name" required>

            <label>Email</label>
            <input type="email" name="email" placeholder="Enter your email" required>

            <label>Password</label>
            <input type="password" name="password" placeholder="Create password" required>

            <button type="submit" style="width:100%;">
                Create Account
            </button>

        </form>

        <p style="margin-top:20px;">
            Already have an account?
            <a class="link" href="{{ url_for('login') }}">Login</a>
        </p>

    </div>

</div>

</body>
</html>
"""


# ---------------- DASHBOARD ----------------

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>

<head>
    <title>ExpenseTracker - Dashboard</title>
""" + STYLE + """
</head>

<body>

<nav class="navbar">

    <div class="logo">
        💰 ExpenseTracker
    </div>

    <div>
        Welcome, {{ user['name'] }} |
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>

</nav>


<div class="container">

    <h1>Dashboard</h1>


    <!-- STAT CARDS -->

    <div class="cards">

        <div class="stat">
            <h3>Total Income</h3>
            <div class="amount income">
                ₹ {{ "%.2f"|format(total_income) }}
            </div>
        </div>

        <div class="stat">
            <h3>Total Expense</h3>
            <div class="amount expense">
                ₹ {{ "%.2f"|format(total_expense) }}
            </div>
        </div>

        <div class="stat">
            <h3>Balance</h3>
            <div class="amount balance">
                ₹ {{ "%.2f"|format(balance) }}
            </div>
        </div>

    </div>


    <!-- ADD TRANSACTION -->

    <div class="card">

        <h2>Add Transaction</h2>

        {% with messages = get_flashed_messages() %}
            {% for message in messages %}
                <div class="alert">{{ message }}</div>
            {% endfor %}
        {% endwith %}

        <form method="POST" action="{{ url_for('add_transaction') }}">

            <div class="form-grid">

                <div>
                    <label>Type</label>

                    <select name="type" required>
                        <option value="Expense">Expense</option>
                        <option value="Income">Income</option>
                    </select>
                </div>


                <div>
                    <label>Category</label>

                    <select name="category" required>

                        <option value="Food">Food</option>
                        <option value="Travel">Travel</option>
                        <option value="Shopping">Shopping</option>
                        <option value="Bills">Bills</option>
                        <option value="Education">Education</option>
                        <option value="Salary">Salary</option>
                        <option value="Other">Other</option>

                    </select>

                </div>


                <div>

                    <label>Amount</label>

                    <input
                        type="number"
                        name="amount"
                        step="0.01"
                        min="0"
                        placeholder="Enter amount"
                        required
                    >

                </div>


                <div>

                    <label>Date</label>

                    <input
                        type="date"
                        name="date"
                        value="{{ today }}"
                        required
                    >

                </div>


                <div class="full">

                    <label>Description</label>

                    <textarea
                        name="description"
                        placeholder="Enter description"
                    ></textarea>

                </div>


                <div class="full">

                    <button type="submit">
                        + Add Transaction
                    </button>

                </div>

            </div>

        </form>

    </div>


    <!-- TRANSACTION HISTORY -->

    <div class="card">

        <h2>Transaction History</h2>

        {% if transactions %}

        <table>

            <thead>

                <tr>

                    <th>Date</th>
                    <th>Type</th>
                    <th>Category</th>
                    <th>Amount</th>
                    <th>Description</th>
                    <th>Action</th>

                </tr>

            </thead>


            <tbody>

                {% for t in transactions %}

                <tr>

                    <td>{{ t['date'] }}</td>

                    <td>
                        {% if t['type'] == 'Income' %}
                            <span class="income">Income</span>
                        {% else %}
                            <span class="expense">Expense</span>
                        {% endif %}
                    </td>

                    <td>{{ t['category'] }}</td>

                    <td>
                        ₹ {{ "%.2f"|format(t['amount']) }}
                    </td>

                    <td>{{ t['description'] or '-' }}</td>

                    <td>

                        <a href="{{ url_for('delete_transaction', transaction_id=t['id']) }}"
                           onclick="return confirm('Delete this transaction?');">

                            <button class="delete-btn">
                                Delete
                            </button>

                        </a>

                    </td>

                </tr>

                {% endfor %}

            </tbody>

        </table>

        {% else %}

            <p>No transactions found.</p>

        {% endif %}

    </div>

</div>

</body>
</html>
"""


# ---------------- ROUTES ----------------

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]

            return redirect(url_for("dashboard"))

        else:

            flash("Invalid email or password.")

    return render_template_string(LOGIN_PAGE)


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users
                (name, email, password, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    password,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )

            conn.commit()

            flash("Account created successfully. Please login.")

            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            flash("Email already registered.")

    return render_template_string(SIGNUP_PAGE)


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()


    transactions = conn.execute(
        """
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()


    income_result = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'Income'
        """,
        (user_id,)
    ).fetchone()


    expense_result = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'Expense'
        """,
        (user_id,)
    ).fetchone()


    total_income = income_result[0]
    total_expense = expense_result[0]

    balance = total_income - total_expense

    conn.close()


    return render_template_string(
        DASHBOARD_PAGE,
        user=user,
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        today=datetime.now().strftime("%Y-%m-%d")
    )


# ---------------- ADD TRANSACTION ----------------

@app.route("/add", methods=["POST"])
def add_transaction():

    if "user_id" not in session:

        return redirect(url_for("login"))


    user_id = session["user_id"]

    transaction_type = request.form["type"]
    category = request.form["category"]
    amount = request.form["amount"]
    description = request.form["description"]
    date = request.form["date"]


    conn = get_db()

    conn.execute(
        """
        INSERT INTO transactions
        (user_id, type, category, amount, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            transaction_type,
            category,
            float(amount),
            description,
            date
        )
    )

    conn.commit()
    conn.close()


    flash("Transaction added successfully.")

    return redirect(url_for("dashboard"))


# ---------------- DELETE TRANSACTION ----------------

@app.route("/delete/<int:transaction_id>")
def delete_transaction(transaction_id):

    if "user_id" not in session:

        return redirect(url_for("login"))


    user_id = session["user_id"]

    conn = get_db()

    conn.execute(
        """
        DELETE FROM transactions
        WHERE id = ? AND user_id = ?
        """,
        (transaction_id, user_id)
    )

    conn.commit()
    conn.close()


    flash("Transaction deleted.")

    return redirect(url_for("dashboard"))


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":

    init_db()

    print("====================================")
    print("     ExpenseTracker Started")
    print("====================================")
    print("Open this link in your browser:")
    print("http://127.0.0.1:5000")
    print("====================================")

    app.run(debug=True)