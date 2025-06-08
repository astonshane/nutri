from flask import current_app as app
from flask import make_response, redirect, render_template, request, url_for

from ..models import Dish, Ingredient, db, fs

def list_dishes():
    """List all dishes."""
    return db.session.execute(db.select(Dish).order_by(Dish.title)).scalars()

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
        dish = Dish(
            title=request.form["title"],
            description=request.form["description"],
        )
        db.session.add(dish)
        db.session.commit()
        return redirect(url_for("dish", id=dish.id))

    dishes = list_dishes()
    return render_template('dishes.html', dishes=dishes)

@app.route("/dishes/<int:id>/ingredients/<int:food_id>/<int:serving_id>/insert", methods=["POST"])
def insert_ingredient(id, food_id, serving_id):
    dish = db.session.get(Dish, id)

    ingredient = Ingredient(
        food_id=food_id,
        serving_id=serving_id,
        quantity=float(request.form['quantity']),
        dish_id=dish.id
    )
    db.session.add(ingredient)
    db.session.commit()
    
    return redirect(url_for("dish", id=dish.id))

@app.route("/dishes/ingredients/<int:id>/delete", methods=["POST"])
def delete_ingredient(id):
    ingredient = db.session.get(Ingredient, id)
    dish = ingredient.dish
    db.session.delete(ingredient)
    db.session.commit()
    
    return redirect(url_for("dish", id=dish.id))


@app.route("/dishes/<int:id>/ingredients", methods=["GET", "POST"])
def search_ingredients(id):
    dish = db.session.get(Dish, id)
    if not dish:
        return make_response("Dish not found", 404)

    if request.method == "POST":
        search_expression = request.form.get("search_expression", "")
        results = fs.search(search_expression, max_results=50, page_number=0)
        return render_template('search.html', search_expression=search_expression, foods=results, dish=dish)

    return render_template('search.html', dish=dish)

@app.route("/dishes/<int:id>/ingredients/<int:food_id>")
def food(id, food_id):
    dish = db.session.get(Dish, id)
    result = fs.food(food_id)
    return render_template('food.html', dish=dish, food=result)