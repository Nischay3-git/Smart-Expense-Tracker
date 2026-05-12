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
def login():
    if request.method == "GET":
        session.clear()   

    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        data = cur.fetchone()

        if data:
            session["user_id"] = data[0]
            session["username"] = user
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
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


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()   
    return redirect("/")

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(debug=True)
