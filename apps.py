from flask import Flask, render_template, request, redirect, session
import matplotlib
matplotlib.use('Agg')   
import matplotlib.pyplot as plt
from models import create_tables, connect_db
import time
from collections import defaultdict
from datetime import datetime


app = Flask(__name__)
app.secret_key = "secret123"

create_tables()

@app.route("/", methods=["GET", "POST"])
def login():# login page k liye
    if request.method == "GET":
        session.clear()   

    if request.method == "POST":#username and password for authentication - apne data sey check karo if present or not
        user = request.form["username"]
        pwd = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        data = cur.fetchone()

        if data:
            session["user_id"] = data[0]
            session["username"] = user
            return redirect("/dashboard")   # agar sahi hai then redirect to dashboard url

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":    #naye user ka credentials store karo
        user = request.form["username"]
        pwd = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users(username,password) VALUES(?,?)", (user, pwd))
        conn.commit()

        return redirect("/")

    return render_template("register.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    # Check if user logged in hai ya nahi
    # Agar session me user_id nahi hai then redirect to login/home page
    if "user_id" not in session:
        return redirect("/")

    # Connecting database
    conn = connect_db()
    cur = conn.cursor()

    # Logged-in user ke expenses fetch
    # Category, amount aur date fetch
    # Latest expenses pehle show honge
    cur.execute("""
        SELECT category, amount, date
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
    """, (session["user_id"],))

    rows = cur.fetchall()

    conn.close()

    # CATEGORY TOTALS
    category_totals = defaultdict(float)
    
    # Traversal for saare records
    for category, amount, _ in rows:
        category_totals[category] += amount
    
    # Sort categories according to total expense
    category_data = sorted(
        category_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )
    # Extract category names ---> separate list
    categories = [x[0] for x in category_data]
    # Extract total amounts ---> separate list
    amounts = [x[1] for x in category_data]

    # PIE CHART
    # Har user ka separate pie chart save hoga
    pie_file = f"pie_{session['user_id']}.png"

    plt.clf()

    if category_data:

        plt.figure(figsize=(5,5))
        # Category-wise expense percentage show karega
        plt.pie(
            amounts,
            labels=categories,
            autopct='%1.1f%%'
        )

        plt.title("Overall Category Distribution")

        plt.savefig(f"static/{pie_file}")

    # MONTHLY TREND
    monthly_totals = defaultdict(float)
    # Loop through expense records
    for _, amount, date in rows:

        dt = datetime.strptime(date, "%Y-%m-%d")

        month_key = dt.strftime("%b %Y")

        monthly_totals[month_key] += amount

    sorted_months = sorted(
        monthly_totals.keys(),
        key=lambda x: datetime.strptime(x, "%b %Y")
    )

    month_labels = sorted_months

    month_values = [
        monthly_totals[m]
        for m in sorted_months
    ]

    # BAR CHART
    bar_file = f"bar_{session['user_id']}.png"

    plt.clf()
    # Check if month data exists ki nhi
    if month_labels:

        plt.figure(figsize=(7,4))

        plt.bar(month_labels, month_values)

        plt.title("Monthly Expense Trend")

        plt.xlabel("Month")
        plt.ylabel("Amount")

        plt.xticks(rotation=45)

        plt.tight_layout()

        plt.savefig(f"static/{bar_file}")

    total = sum(month_values)

    version = int(time.time())
    
    # dashboard.html pe bhejo
    return render_template(
        "dashboard.html",
        total=total,
        category_data=category_data,
        version=version,
        pie_file=pie_file,
        bar_file=bar_file
    )

# ---------------- MONTHLY ANALYTICS ----------------
@app.route("/monthly")
def monthly():
    # Check if user is logged in
    # Agar user session me nahi hai, redirect to home/login page
    if "user_id" not in session:
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT category, amount, date
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
    """, (session["user_id"],))

    rows = cur.fetchall()

    conn.close()

    monthly_expenses = defaultdict(list)
    monthly_totals = defaultdict(float)

    for category, amount, date in rows:

        dt = datetime.strptime(date, "%Y-%m-%d")

        month_key = dt.strftime("%B %Y")

        monthly_expenses[month_key].append({
            "category": category,
            "amount": amount,
            "date": date
        })

        monthly_totals[month_key] += amount
    # Sort months in descending order (latest month first)
    sorted_months = sorted(
        monthly_expenses.keys(),
        key=lambda x: datetime.strptime(x, "%B %Y"),
        reverse=True
    )

    os.makedirs("static/monthly_charts", exist_ok=True)

    monthly_chart_files = {}

    for month in sorted_months:

        expenses = monthly_expenses[month]

        cat_totals = defaultdict(float)

        for e in expenses:
            cat_totals[e["category"]] += e["amount"]

        labels = list(cat_totals.keys())
        values = list(cat_totals.values())

        plt.clf()

        if values:

            plt.figure(figsize=(4,4))

            plt.pie(
                values,
                labels=None,
                autopct='%1.1f%%'
            )

            if len(labels) > 1:

                plt.legend(
                    labels,
                    loc="center left",
                    bbox_to_anchor=(1,0.5),
                    fontsize=8
                )

            plt.title(month)

            filename = (
                f"monthly_charts/"
                f"user_{session['user_id']}_"
                f"{month.replace(' ', '_')}.png"
            )

            full_path = os.path.join("static", filename)

            plt.savefig(
                full_path,
                bbox_inches='tight'
            )

            monthly_chart_files[month] = filename
    # timestamp for refreshing charts
    version = int(time.time())

    # monthly.html pe sb kuch send
    return render_template(
        "monthly.html",
        monthly_expenses=monthly_expenses,
        monthly_totals=monthly_totals,
        sorted_months=sorted_months,
        monthly_chart_files=monthly_chart_files,
        version=version
    )

# ---------------- ADD EXPENSE ----------------
@app.route("/add", methods=["GET", "POST"])
def add():

    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":

        try:

            amount = float(request.form["amount"])

            category = request.form["category"]

            date = request.form["date"]

            conn = connect_db()
            cur = conn.cursor()

            cur.execute('''
            INSERT INTO expenses(
                user_id,
                amount,
                category,
                date
            )
            VALUES (?, ?, ?, ?)
            ''', (
                session["user_id"],
                amount,
                category,
                date
            ))

            conn.commit()
            conn.close()

            return redirect("/dashboard")

        except Exception as e:

            return f"Error: {e}"

    return render_template("add.html")
# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()   #agar user logout karey toh login page  mey jao wapis
    return redirect("/")

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)
