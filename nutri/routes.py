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

@app.route("/dish/<int:id>", methods=["GET"])
def dish(id):        
    dish = db.session.get(Dish, id)
    if not dish:
        return make_response("Dish not found", 404)
    return render_template('dish.html', dish=dish)

@app.route("/dish/<int:id>/delete", methods=["POST"])
def delete_dish(id):
    dish = db.session.get(Dish, id)
    if not dish:
        return make_response("Dish not found", 404)
    db.session.delete(dish)
    db.session.commit()
    # set flash message?
    return redirect(url_for("dishes"))

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
        return redirect(url_for("dish", id=dish.id))

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