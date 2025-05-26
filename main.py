from dotenv import load_dotenv
import os
from fatsecret.fatsecret import Fatsecret
from flask import Flask, request, render_template
    
load_dotenv()
fs = Fatsecret(os.getenv("FATSECRET_CLIENT_ID"), os.getenv("FATSECRET_CLIENT_SECRET"))
app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template('index.html')

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