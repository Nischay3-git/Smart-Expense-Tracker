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
