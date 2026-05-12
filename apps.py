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
  
