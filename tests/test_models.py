"""Unit tests for Dish and Ingredient nutrition calculation logic."""
import pytest
from nutri.models import Dish, Ingredient


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
