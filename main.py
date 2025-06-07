from dotenv import load_dotenv
import os
from fatsecret.fatsecret import Fatsecret
from flask import Flask, request, render_template, g
from dish import Dish
import sqlite3

DATABASE = './database.db'
    
load_dotenv()
fs = Fatsecret(os.getenv("FATSECRET_CLIENT_ID"), os.getenv("FATSECRET_CLIENT_SECRET"))
app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

init_db()


@app.route("/")
def hello_world():
    dishes = []
    for dish in query_db('select * from dishes'):
        dishes.append(Dish(dish))
    return render_template('index.html', dishes=dishes)

@app.route("/search", methods=["GET", "POST"])
def ingredient_search():
    search_expression = "apple"
    if request.method == "POST":
        search_expression = request.form.get("search_expression", search_expression)
    results = fs.search(search_expression, max_results=50, page_number=0)
    return render_template('search.html', search_expression=search_expression, foods=results)

@app.route("/food/<int:food_id>")
def food(food_id):
    result = fs.food(food_id)
    print(f"Food ID: {food_id}, Result: {result}")
    return render_template('food.html', food=result)