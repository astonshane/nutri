import logging

from flask import current_app as app
from flask import flash, make_response, redirect, render_template, request, url_for

logger = logging.getLogger(__name__)

from ..helpers import static_nutrition_info
from ..models import CustomFood, Dish, Ingredient, db, fs

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
    url = request.form.get("url", "").strip()
    if url and not (url.startswith("http://") or url.startswith("https://")):
        flash("Recipe URL must start with http:// or https://")
        return redirect(url_for("dish", id=dish.id))
    dish.url = url or None
    dish.portions = int(request.form.get("portions", dish.portions))
    db.session.commit()
    flash("Dish updated.")
    return redirect(url_for("dish", id=dish.id))

@app.route("/dishes", methods=["GET", "POST"])
def dishes():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if url and not (url.startswith("http://") or url.startswith("https://")):
            url = None
        dish = Dish(
            title=request.form["title"],
            description=request.form["description"],
            url=url or None,
            portions=int(request.form.get("servings", 1)),
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

@app.route("/dishes/ingredients/<int:id>/update", methods=["POST"])
def update_ingredient(id):
    ingredient = db.session.get(Ingredient, id)
    if not ingredient:
        return make_response("Ingredient not found", 404)
    try:
        quantity = float(request.form.get("quantity", 0))
    except ValueError:
        return make_response("Invalid quantity", 400)
    if quantity <= 0:
        return make_response("Quantity must be positive", 400)
    ingredient.quantity = quantity
    db.session.commit()
    return ("", 204)

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


@app.route("/dishes/<int:dish_id>/ingredients/custom/<int:cf_id>", methods=["GET"])
def custom_food_detail(dish_id, cf_id):
    dish = db.session.get(Dish, dish_id)
    if not dish:
        return make_response("Dish not found", 404)
    custom_food = db.session.get(CustomFood, cf_id)
    if not custom_food:
        return make_response("Custom food not found", 404)
    return render_template('custom_foods/detail.html', dish=dish, custom_food=custom_food)


@app.route("/dishes/<int:dish_id>/ingredients/custom/<int:cf_id>/insert", methods=["POST"])
def insert_custom_ingredient(dish_id, cf_id):
    dish = db.session.get(Dish, dish_id)
    if not dish:
        return make_response("Dish not found", 404)
    custom_food = db.session.get(CustomFood, cf_id)
    if not custom_food:
        return make_response("Custom food not found", 404)
    try:
        quantity = float(request.form.get('quantity', 1.0))
        if quantity <= 0:
            quantity = 1.0
    except (ValueError, TypeError):
        quantity = 1.0
    ingredient = Ingredient(
        dish_id=dish.id,
        food_id=None,
        serving_id=None,
        custom_food_id=custom_food.id,
        food_name=custom_food.name,
        serving_description=custom_food.serving_description,
        quantity=quantity,
        **{key: getattr(custom_food, key) for key in static_nutrition_info.keys()}
    )
    db.session.add(ingredient)
    db.session.commit()
    return redirect(url_for('dish', id=dish_id))


@app.route("/dishes/<int:id>/ingredients", methods=["GET", "POST"])
def search_ingredients(id):
    dish = db.session.get(Dish, id)
    if not dish:
        return make_response("Dish not found", 404)

    if request.method == "POST":
        search_expression = request.form.get("search_expression", "")
        page = max(0, min(int(request.form.get("page", 0)), 100))

        # Query custom foods first so they appear even if FatSecret fails
        custom_results = db.session.execute(
            db.select(CustomFood).where(CustomFood.name.ilike(f'%{search_expression}%'))
        ).scalars().all()
        custom_food_results = [
            {
                'is_custom': True,
                'id': cf.id,
                'food_name': cf.name,
                'food_url': None,
                'brand_name': 'Custom',
            }
            for cf in custom_results
        ]

        try:
            fs_results = fs.search(search_expression, max_results=50, page_number=page)
        except Exception as exc:
            logger.warning("FatSecret search failed: %s", exc)
            fs_results = []

        # Combine: custom foods first, then FatSecret results
        all_results = custom_food_results + fs_results

        return render_template(
            'search.html',
            search_expression=search_expression,
            foods=all_results,
            dish=dish,
            page=page,
            has_next=len(fs_results) == 50,
        )

    return render_template('search.html', dish=dish)

@app.route("/dishes/<int:id>/ingredients/<int:food_id>")
def food(id, food_id):
    dish = db.session.get(Dish, id)
    result = fs.food(food_id)
    return render_template('food.html', dish=dish, food=result)