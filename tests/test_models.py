"""Unit tests for Dish and Ingredient nutrition calculation logic."""
import pytest
from nutri import db as _db
from nutri.models import CustomFood, Dish, Ingredient


def make_ingredient(**kwargs):
    defaults = dict(
        food_id=1, serving_id=1, quantity=1.0, dish_id=1,
        calories=0.0, fat=0.0, sodium=0.0, carbohydrate=0.0, fiber=0.0, protein=0.0,
    )
    defaults.update(kwargs)
    return Ingredient(**defaults)


class TestIngredientNutrition:
    def test_scales_by_quantity(self, app):
        with app.app_context():
            ing = make_ingredient(quantity=2.0, calories=100.0, protein=10.0)
            result = ing.nutrition()
            assert result["calories"] == 200.0
            assert result["protein"] == 20.0

    def test_all_fields_scaled(self, app):
        with app.app_context():
            ing = make_ingredient(
                quantity=3.0,
                calories=10.0, fat=2.0, sodium=50.0,
                carbohydrate=5.0, fiber=1.0, protein=4.0,
            )
            result = ing.nutrition()
            assert result == {
                "calories": 30.0, "fat": 6.0, "sodium": 150.0,
                "carbohydrate": 15.0, "fiber": 3.0, "protein": 12.0,
            }

    def test_none_fields_treated_as_zero(self, app):
        with app.app_context():
            ing = make_ingredient(
                quantity=5.0,
                calories=None, fat=None, sodium=None,
                carbohydrate=None, fiber=None, protein=None,
            )
            result = ing.nutrition()
            assert all(v == 0.0 for v in result.values())

    def test_fractional_quantity(self, app):
        with app.app_context():
            ing = make_ingredient(quantity=0.5, calories=200.0)
            assert ing.nutrition()["calories"] == 100.0


class TestDishNutrition:
    def test_sums_ingredients(self, app):
        with app.app_context():
            dish = Dish(title="Test", portions=1)
            dish.ingredients = [
                make_ingredient(quantity=1.0, calories=100.0, protein=5.0),
                make_ingredient(quantity=1.0, calories=200.0, protein=10.0),
            ]
            result = dish.nutrition()
            assert result["calories"] == 300.0
            assert result["protein"] == 15.0

    def test_empty_dish_returns_zeros(self, app):
        with app.app_context():
            dish = Dish(title="Empty", portions=1)
            dish.ingredients = []
            result = dish.nutrition()
            assert all(v == 0 for v in result.values())

    def test_ingredient_quantities_applied_before_sum(self, app):
        with app.app_context():
            dish = Dish(title="Test", portions=1)
            dish.ingredients = [
                make_ingredient(quantity=2.0, calories=50.0),
                make_ingredient(quantity=3.0, calories=40.0),
            ]
            assert dish.nutrition()["calories"] == 220.0


class TestDishNutritionPerPortion:
    def test_divides_by_portions(self, app):
        with app.app_context():
            dish = Dish(title="Test", portions=4)
            dish.ingredients = [make_ingredient(quantity=1.0, calories=400.0)]
            assert dish.nutrition_per_portion()["calories"] == 100.0

    def test_single_portion(self, app):
        with app.app_context():
            dish = Dish(title="Test", portions=1)
            dish.ingredients = [make_ingredient(quantity=1.0, calories=300.0)]
            assert dish.nutrition_per_portion()["calories"] == 300.0

    def test_zero_portions_falls_back_to_one(self, app):
        with app.app_context():
            dish = Dish(title="Test", portions=0)
            dish.ingredients = [make_ingredient(quantity=1.0, calories=200.0)]
            # `or 1` guard prevents division by zero
            assert dish.nutrition_per_portion()["calories"] == 200.0


def make_custom_food(**kwargs):
    defaults = dict(
        name="Test Food",
        serving_description="100g",
        calories=100.0,
        fat=2.0,
        sodium=50.0,
        carbohydrate=10.0,
        fiber=1.0,
        protein=8.0,
    )
    defaults.update(kwargs)
    return CustomFood(**defaults)


class TestCustomFoodCreation:
    def test_creates_with_required_fields(self, app):
        with app.app_context():
            cf = make_custom_food()
            assert cf.name == "Test Food"
            assert cf.serving_description == "100g"

    def test_repr(self, app):
        with app.app_context():
            cf = make_custom_food(name="Oats")
            # id is None before DB flush, but repr should not raise
            assert "Oats" in repr(cf)

    def test_persists_to_db(self, app):
        with app.app_context():
            cf = make_custom_food(name="Brown Rice")
            _db.session.add(cf)
            _db.session.commit()
            fetched = _db.session.get(CustomFood, cf.id)
            assert fetched.name == "Brown Rice"

    def test_all_nutrition_fields_stored(self, app):
        with app.app_context():
            cf = make_custom_food(
                calories=200.0, fat=5.0, sodium=120.0,
                carbohydrate=30.0, fiber=3.0, protein=15.0,
            )
            _db.session.add(cf)
            _db.session.commit()
            fetched = _db.session.get(CustomFood, cf.id)
            assert fetched.calories == 200.0
            assert fetched.fat == 5.0
            assert fetched.sodium == 120.0
            assert fetched.carbohydrate == 30.0
            assert fetched.fiber == 3.0
            assert fetched.protein == 15.0


class TestCustomFoodNutritionFields:
    def test_all_six_nutrition_fields_present(self, app):
        with app.app_context():
            cf = make_custom_food()
            for field in ("calories", "fat", "sodium", "carbohydrate", "fiber", "protein"):
                assert hasattr(cf, field), f"Missing field: {field}"

    def test_inherits_base_model_methods(self, app):
        with app.app_context():
            cf = make_custom_food()
            assert "calories" in cf.static_nutrition_keys()
            assert cf.static_nutrition_label("calories") == "Cal (kcal)"

    def test_fractional_nutrition_values(self, app):
        with app.app_context():
            cf = make_custom_food(calories=99.9, fat=1.5, protein=7.3)
            _db.session.add(cf)
            _db.session.commit()
            fetched = _db.session.get(CustomFood, cf.id)
            assert abs(fetched.calories - 99.9) < 0.001
            assert abs(fetched.fat - 1.5) < 0.001
            assert abs(fetched.protein - 7.3) < 0.001


class TestCustomFoodIngredientRelationship:
    def test_ingredient_linked_to_custom_food(self, app):
        with app.app_context():
            # Create a dish and a custom food
            dish = Dish(title="Custom Dish", portions=1)
            _db.session.add(dish)
            _db.session.flush()

            cf = make_custom_food(name="Homemade Sauce")
            _db.session.add(cf)
            _db.session.flush()

            ing = Ingredient(
                custom_food_id=cf.id,
                quantity=2.0,
                dish_id=dish.id,
                food_name="Homemade Sauce",
                serving_description="100g",
                calories=50.0,
                fat=1.0,
                sodium=20.0,
                carbohydrate=8.0,
                fiber=0.5,
                protein=3.0,
            )
            _db.session.add(ing)
            _db.session.commit()

            fetched_ing = _db.session.get(Ingredient, ing.id)
            assert fetched_ing.custom_food_id == cf.id
            assert fetched_ing.food_id is None
            assert fetched_ing.serving_id is None

    def test_custom_food_has_ingredients_backref(self, app):
        with app.app_context():
            dish = Dish(title="Backref Dish", portions=1)
            _db.session.add(dish)
            _db.session.flush()

            cf = make_custom_food(name="My Dressing")
            _db.session.add(cf)
            _db.session.flush()

            ing = Ingredient(
                custom_food_id=cf.id,
                quantity=1.0,
                dish_id=dish.id,
                food_name="My Dressing",
                serving_description="1 tbsp",
                calories=45.0,
                fat=4.5,
                sodium=90.0,
                carbohydrate=1.0,
                fiber=0.0,
                protein=0.5,
            )
            _db.session.add(ing)
            _db.session.commit()

            fetched_cf = _db.session.get(CustomFood, cf.id)
            assert len(fetched_cf.ingredients) == 1
            assert fetched_cf.ingredients[0].id == ing.id

    def test_ingredient_without_custom_food_has_none(self, app):
        with app.app_context():
            dish = Dish(title="Standard Dish", portions=1)
            _db.session.add(dish)
            _db.session.flush()

            ing = Ingredient(
                food_id=42,
                serving_id=99,
                quantity=1.0,
                dish_id=dish.id,
                calories=100.0,
                fat=2.0,
                sodium=30.0,
                carbohydrate=15.0,
                fiber=1.0,
                protein=5.0,
            )
            _db.session.add(ing)
            _db.session.commit()

            fetched = _db.session.get(Ingredient, ing.id)
            assert fetched.custom_food_id is None
            assert fetched.food_id == 42
