from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from ..helpers import static_nutrition_info
from ..models import CustomFood, Ingredient, db

bp = Blueprint('custom_foods', __name__)

NUTRITION_FIELDS = list(static_nutrition_info.keys())


def _parse_nutrition_form(form):
    """Parse and validate nutrition float fields from a form dict.

    Returns (data_dict, error_message).  error_message is None on success.
    """
    data = {}
    for field in NUTRITION_FIELDS:
        raw = form.get(field, '').strip()
        if raw == '':
            return None, f"'{field}' is required."
        try:
            data[field] = float(raw)
        except ValueError:
            return None, f"'{field}' must be a number."
    return data, None


@bp.route('/', methods=['GET'])
def index():
    """List all custom foods."""
    foods = db.session.execute(
        db.select(CustomFood).order_by(CustomFood.name)
    ).scalars().all()
    return render_template('custom_foods/index.html', foods=foods)


@bp.route('/new', methods=['GET'])
def new():
    """Show create form."""
    dish_id = request.args.get('dish_id', type=int)
    return render_template('custom_foods/form.html', custom_food=None, dish_id=dish_id)


@bp.route('/', methods=['POST'])
def create():
    """Save a new custom food."""
    name = request.form.get('name', '').strip()
    serving_description = request.form.get('serving_description', '').strip()

    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('custom_foods.new'))
    if not serving_description:
        flash('Serving description is required.', 'danger')
        return redirect(url_for('custom_foods.new'))

    nutrition, error = _parse_nutrition_form(request.form)
    if error:
        flash(error, 'danger')
        return redirect(url_for('custom_foods.new'))

    dish_id = request.form.get('dish_id', type=int)

    food = CustomFood(name=name, serving_description=serving_description, **nutrition)
    db.session.add(food)
    try:
        db.session.commit()
        flash(f'"{food.name}" created.', 'success')
        if dish_id:
            return redirect(url_for('custom_food_detail', dish_id=dish_id, cf_id=food.id))
        return redirect(url_for('custom_foods.index'))
    except IntegrityError:
        db.session.rollback()
        flash('A custom food with that name already exists.', 'danger')
        return redirect(url_for('custom_foods.new', dish_id=dish_id) if dish_id else url_for('custom_foods.new'))


@bp.route('/<int:id>/edit', methods=['GET'])
def edit(id):
    """Show edit form."""
    food = db.session.get(CustomFood, id)
    if not food:
        return make_response('Custom food not found', 404)
    return render_template('custom_foods/form.html', custom_food=food)


@bp.route('/<int:id>/update', methods=['POST'])
def update(id):
    """Save edits to an existing custom food."""
    food = db.session.get(CustomFood, id)
    if not food:
        return make_response('Custom food not found', 404)

    name = request.form.get('name', '').strip()
    serving_description = request.form.get('serving_description', '').strip()

    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('custom_foods.edit', id=id))
    if not serving_description:
        flash('Serving description is required.', 'danger')
        return redirect(url_for('custom_foods.edit', id=id))

    nutrition, error = _parse_nutrition_form(request.form)
    if error:
        flash(error, 'danger')
        return redirect(url_for('custom_foods.edit', id=id))

    food.name = name
    food.serving_description = serving_description
    for field, value in nutrition.items():
        setattr(food, field, value)
    try:
        db.session.commit()
        flash(f'"{food.name}" updated.', 'success')
        return redirect(url_for('custom_foods.index'))
    except IntegrityError:
        db.session.rollback()
        flash('A custom food with that name already exists.', 'danger')
        return redirect(url_for('custom_foods.edit', id=id))


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete a custom food, with a warning if it is used by any ingredients."""
    food = db.session.get(CustomFood, id)
    if not food:
        return make_response('Custom food not found', 404)

    usage_count = db.session.execute(
        db.select(db.func.count()).select_from(Ingredient).where(
            Ingredient.custom_food_id == id
        )
    ).scalar()

    if usage_count > 0:
        if request.form.get('confirm') != '1':
            flash(
                f'"{food.name}" is used by {usage_count} dish ingredient(s). '
                'Submit again with confirmation to delete it. '
                'Existing dish ingredients using it will be preserved.',
                'warning',
            )
            return redirect(url_for('custom_foods.index'))
        name = food.name
        db.session.delete(food)
        db.session.commit()
        flash(
            f'"{name}" deleted. Existing dish ingredients using it have been preserved.',
            'success',
        )
        return redirect(url_for('custom_foods.index'))

    # Not used anywhere — delete immediately
    name = food.name
    db.session.delete(food)
    db.session.commit()
    flash(f'"{name}" deleted.', 'success')
    return redirect(url_for('custom_foods.index'))
