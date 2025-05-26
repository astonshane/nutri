from dotenv import load_dotenv
import os
from fatsecret import Fatsecret
from flask import Flask, render_template
    
load_dotenv()
fs = Fatsecret(os.getenv("FATSECRET_CLIENT_ID"), os.getenv("FATSECRET_CLIENT_SECRET"))
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "hello world"

@app.route("/search/<search_expression>")
def search(search_expression):
    results = fs.search(search_expression, max_results=50, page_number=0)
    return render_template('search.html', search_expression=search_expression, results=results)

@app.route("/food/<int:food_id>")
def food(food_id):
    result = fs.food(food_id)
    print(f"Food ID: {food_id}, Result: {result}")
    return render_template('food.html', food=result)