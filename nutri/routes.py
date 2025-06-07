from datetime import datetime

from flask import current_app as app
from flask import make_response, redirect, render_template, request, url_for

from .models import Dish, db

def list_dishes():
    """List all dishes."""
    return db.session.execute(db.select(Dish).order_by(Dish.title)).scalars()

@app.route("/")
def index():
    return render_template('index.html', dishes=list_dishes())

@app.route("/dishes", methods=["GET", "POST"])
def dishes():
    if request.method == "POST":
        print(request.form)
        dish = Dish(
            title=request.form["title"],
            description=request.form["description"],
        )
        db.session.add(dish)
        db.session.commit()
        # return redirect(url_for("user_detail", id=user.id))

    dishes = list_dishes()
    return render_template('dishes.html', dishes=dishes)

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