from flask import current_app as app
from flask import flash, make_response, redirect, render_template, request, url_for

from ..helpers import static_nutrition_info
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
    title = dish.title
    db.session.delete(dish)
    db.session.commit()
    flash(f'"{title}" deleted.')
    return redirect(url_for("dishes"))

@app.route("/dish/<int:id>/update", methods=["POST"])
def update_dish(id):
    dish = db.session.get(Dish, id)
    if not dish:
        return make_response("Dish not found", 404)
    dish.title = request.form.get("title", dish.title).strip() or dish.title
    dish.description = request.form.get("description", dish.description)
    dish.url = request.form.get("url", dish.url).strip() or None
    dish.portions = int(request.form.get("portions", dish.portions))
    db.session.commit()
    flash("Dish updated.")
    return redirect(url_for("dish", id=dish.id))

@app.route("/dishes", methods=["GET", "POST"])
def dishes():
    if request.method == "POST":
        dish = Dish(
            title=request.form["title"],
            description=request.form["description"],
            portions = int(request.form.get("servings", 1))  # Default to 1 serving if not provided
        )
        db.session.add(dish)
        db.session.commit()
        return redirect(url_for("dish", id=dish.id))

    dishes = list_dishes()
    return render_template('dishes.html', dishes=dishes)

@app.route("/dishes/<int:id>/ingredients/<int:food_id>/<int:serving_id>/insert", methods=["POST"])
def insert_ingredient(id, food_id, serving_id):
    dish = db.session.get(Dish, id)
    if not dish:
        return make_response("Dish not found", 404)

    food = fs.food(food_id)
    serving = food.serving(serving_id)

    ingredient = Ingredient(
        food_id=food_id,
        serving_id=serving_id,
        quantity=float(request.form['quantity']),
        dish_id=dish.id,
        food_name=food.name,
        food_url=food.url,
        serving_description=serving.description,
        **{key: serving.nutrition_info[key] for key in static_nutrition_info.keys()}
    )
    db.session.add(ingredient)
    db.session.commit()

    return redirect(url_for("dish", id=dish.id))

@app.route("/dishes/ingredients/<int:id>/delete", methods=["POST"])
def delete_ingredient(id):
    ingredient = db.session.get(Ingredient, id)
    if not ingredient:
        return make_response("Ingredient not found", 404)
    dish_id = ingredient.dish_id
    food_name = ingredient.food_name
    db.session.delete(ingredient)
    db.session.commit()
    flash(f'"{food_name}" removed.')
    return redirect(url_for("dish", id=dish_id))


@app.route("/dishes/<int:id>/ingredients", methods=["GET", "POST"])
def search_ingredients(id):
    dish = db.session.get(Dish, id)
    if not dish:
        return make_response("Dish not found", 404)

    if request.method == "POST":
        search_expression = request.form.get("search_expression", "")
        page = int(request.form.get("page", 0))
        results = fs.search(search_expression, max_results=50, page_number=page)
        return render_template(
            'search.html',
            search_expression=search_expression,
            foods=results,
            dish=dish,
            page=page,
            has_next=len(results) == 50,
        )

    return render_template('search.html', dish=dish)

@app.route("/dishes/<int:id>/ingredients/<int:food_id>")
def food(id, food_id):
    dish = db.session.get(Dish, id)
    result = fs.food(food_id)
    return render_template('food.html', dish=dish, food=result)