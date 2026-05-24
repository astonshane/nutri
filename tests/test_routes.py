"""Route integration tests using the Flask test client."""
from unittest.mock import MagicMock, patch

import pytest

from nutri import db as _db
from nutri.models import CustomFood, Dish, Ingredient


class TestDishList:
    def test_get_returns_200(self, client):
        assert client.get("/dishes").status_code == 200

    def test_post_creates_dish_and_redirects(self, client, app):
        resp = client.post("/dishes", data={
            "title": "New Dish", "description": "yum", "url": "", "servings": "2",
        })
        assert resp.status_code == 302
        with app.app_context():
            dish = _db.session.execute(_db.select(Dish)).scalar_one()
            assert dish.title == "New Dish"
            assert dish.portions == 2

    def test_post_strips_invalid_url(self, client, app):
        client.post("/dishes", data={
            "title": "Dish", "description": "", "url": "not-a-url", "servings": "1",
        })
        with app.app_context():
            dish = _db.session.execute(_db.select(Dish)).scalar_one()
            assert dish.url is None

    def test_post_stores_valid_https_url(self, client, app):
        client.post("/dishes", data={
            "title": "Dish", "description": "", "url": "https://example.com/recipe", "servings": "1",
        })
        with app.app_context():
            dish = _db.session.execute(_db.select(Dish)).scalar_one()
            assert dish.url == "https://example.com/recipe"

    def test_post_stores_valid_http_url(self, client, app):
        client.post("/dishes", data={
            "title": "Dish", "description": "", "url": "http://example.com/recipe", "servings": "1",
        })
        with app.app_context():
            dish = _db.session.execute(_db.select(Dish)).scalar_one()
            assert dish.url == "http://example.com/recipe"


class TestDishDetail:
    def test_get_existing_dish_returns_200(self, client, dish):
        assert client.get(f"/dish/{dish}").status_code == 200

    def test_get_nonexistent_dish_returns_404(self, client):
        assert client.get("/dish/9999").status_code == 404


class TestUpdateDish:
    def test_updates_fields(self, client, dish, app):
        client.post(f"/dish/{dish}/update", data={
            "title": "Updated", "description": "new desc", "url": "", "portions": "4",
        })
        with app.app_context():
            d = _db.session.get(Dish, dish)
            assert d.title == "Updated"
            assert d.portions == 4

    def test_invalid_url_flashes_error_and_does_not_update(self, client, dish, app):
        resp = client.post(f"/dish/{dish}/update", data={
            "title": "Pasta", "description": "", "url": "ftp://bad.com", "portions": "2",
        }, follow_redirects=True)
        assert b"must start with http" in resp.data
        with app.app_context():
            d = _db.session.get(Dish, dish)
            assert d.url is None  # was never set

    def test_nonexistent_dish_returns_404(self, client):
        assert client.post("/dish/9999/update", data={
            "title": "x", "description": "", "url": "", "portions": "1",
        }).status_code == 404


class TestDeleteDish:
    def test_delete_redirects(self, client, dish):
        assert client.post(f"/dish/{dish}/delete").status_code == 302

    def test_delete_removes_dish(self, client, dish, app):
        client.post(f"/dish/{dish}/delete")
        with app.app_context():
            assert _db.session.get(Dish, dish) is None

    def test_delete_cascades_to_ingredients(self, client, dish_with_ingredient, app):
        dish_id, ing_id = dish_with_ingredient
        client.post(f"/dish/{dish_id}/delete")
        with app.app_context():
            assert _db.session.get(Ingredient, ing_id) is None

    def test_nonexistent_dish_returns_404(self, client):
        assert client.post("/dish/9999/delete").status_code == 404


class TestUpdateIngredient:
    def test_updates_quantity(self, client, dish_with_ingredient, app):
        dish_id, ing_id = dish_with_ingredient
        resp = client.post(f"/dishes/ingredients/{ing_id}/update", data={"quantity": "3.5"})
        assert resp.status_code == 204
        with app.app_context():
            assert _db.session.get(Ingredient, ing_id).quantity == 3.5

    def test_zero_quantity_returns_400(self, client, dish_with_ingredient):
        _, ing_id = dish_with_ingredient
        assert client.post(
            f"/dishes/ingredients/{ing_id}/update", data={"quantity": "0"}
        ).status_code == 400

    def test_negative_quantity_returns_400(self, client, dish_with_ingredient):
        _, ing_id = dish_with_ingredient
        assert client.post(
            f"/dishes/ingredients/{ing_id}/update", data={"quantity": "-1"}
        ).status_code == 400

    def test_non_numeric_quantity_returns_400(self, client, dish_with_ingredient):
        _, ing_id = dish_with_ingredient
        assert client.post(
            f"/dishes/ingredients/{ing_id}/update", data={"quantity": "abc"}
        ).status_code == 400

    def test_nonexistent_ingredient_returns_404(self, client):
        assert client.post(
            "/dishes/ingredients/9999/update", data={"quantity": "1"}
        ).status_code == 404


class TestDeleteIngredient:
    def test_delete_removes_ingredient(self, client, dish_with_ingredient, app):
        dish_id, ing_id = dish_with_ingredient
        client.post(f"/dishes/ingredients/{ing_id}/delete")
        with app.app_context():
            assert _db.session.get(Ingredient, ing_id) is None

    def test_delete_redirects_to_dish(self, client, dish_with_ingredient):
        dish_id, ing_id = dish_with_ingredient
        resp = client.post(f"/dishes/ingredients/{ing_id}/delete")
        assert resp.status_code == 302
        assert f"/dish/{dish_id}" in resp.headers["Location"]

    def test_nonexistent_ingredient_returns_404(self, client):
        assert client.post("/dishes/ingredients/9999/delete").status_code == 404


class TestInsertIngredient:
    def _mock_fs(self):
        mock_food = MagicMock()
        mock_food.name = "Chicken Breast"
        mock_food.url = "http://example.com/chicken"
        mock_serving = MagicMock()
        mock_serving.description = "100g serving"
        mock_serving.nutrition_info = {
            "calories": 165.0, "fat": 3.6, "sodium": 74.0,
            "carbohydrate": 0.0, "fiber": 0.0, "protein": 31.0,
        }
        mock_food.serving.return_value = mock_serving
        return mock_food

    def test_inserts_ingredient_with_nutrition(self, client, dish, app):
        with patch("nutri.routes.dishes.fs") as mock_fs:
            mock_fs.food.return_value = self._mock_fs()
            resp = client.post(
                f"/dishes/{dish}/ingredients/100/200/insert",
                data={"quantity": "1.5"},
            )
        assert resp.status_code == 302
        with app.app_context():
            ing = _db.session.execute(_db.select(Ingredient)).scalar_one()
            assert ing.food_id == 100
            assert ing.serving_id == 200
            assert ing.quantity == 1.5
            assert ing.calories == 165.0
            assert ing.protein == 31.0

    def test_nonexistent_dish_returns_404(self, client):
        with patch("nutri.routes.dishes.fs") as mock_fs:
            mock_fs.food.return_value = self._mock_fs()
            resp = client.post(
                "/dishes/9999/ingredients/100/200/insert",
                data={"quantity": "1"},
            )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Custom Foods
# ---------------------------------------------------------------------------

_NUTRITION = {
    'calories': '100',
    'fat': '2.5',
    'sodium': '50',
    'carbohydrate': '10',
    'fiber': '1',
    'protein': '5',
}


@pytest.fixture
def custom_food(app):
    """Create a CustomFood and return its id."""
    with app.app_context():
        cf = CustomFood(
            name='Test Oat',
            serving_description='100g',
            calories=100.0,
            fat=2.5,
            sodium=50.0,
            carbohydrate=10.0,
            fiber=1.0,
            protein=5.0,
        )
        _db.session.add(cf)
        _db.session.commit()
        return cf.id


@pytest.fixture
def custom_food_in_use(app):
    """Create a CustomFood referenced by an Ingredient; return (cf_id, dish_id, ing_id)."""
    with app.app_context():
        cf = CustomFood(
            name='Used Food',
            serving_description='1 cup',
            calories=200.0,
            fat=5.0,
            sodium=100.0,
            carbohydrate=20.0,
            fiber=2.0,
            protein=10.0,
        )
        _db.session.add(cf)
        _db.session.flush()
        d = Dish(title='Test Dish', portions=1)
        _db.session.add(d)
        _db.session.flush()
        ing = Ingredient(
            quantity=1.0,
            dish_id=d.id,
            custom_food_id=cf.id,
            food_name='Used Food',
            serving_description='1 cup',
            calories=200.0,
            fat=5.0,
            sodium=100.0,
            carbohydrate=20.0,
            fiber=2.0,
            protein=10.0,
        )
        _db.session.add(ing)
        _db.session.commit()
        return cf.id, d.id, ing.id


class TestCustomFoodList:
    def test_get_returns_200(self, client):
        assert client.get('/custom-foods/').status_code == 200

    def test_lists_existing_foods(self, client, custom_food, app):
        resp = client.get('/custom-foods/')
        assert resp.status_code == 200


class TestCustomFoodCreate:
    def test_get_new_form_returns_200(self, client):
        assert client.get('/custom-foods/new').status_code == 200

    def test_post_valid_creates_food_and_redirects(self, client, app):
        resp = client.post('/custom-foods/', data={
            'name': 'New Food', 'serving_description': '100g', **_NUTRITION,
        })
        assert resp.status_code == 302
        with app.app_context():
            cf = _db.session.execute(_db.select(CustomFood)).scalar_one()
            assert cf.name == 'New Food'
            assert cf.calories == 100.0

    def test_post_missing_name_redirects_without_creating(self, client, app):
        resp = client.post('/custom-foods/', data={
            'name': '', 'serving_description': '100g', **_NUTRITION,
        })
        assert resp.status_code == 302
        with app.app_context():
            count = _db.session.execute(
                _db.select(_db.func.count()).select_from(CustomFood)
            ).scalar()
            assert count == 0

    def test_post_missing_nutrition_field_redirects_without_creating(self, client, app):
        data = {'name': 'Food', 'serving_description': '100g', **_NUTRITION}
        del data['calories']
        resp = client.post('/custom-foods/', data=data)
        assert resp.status_code == 302
        with app.app_context():
            count = _db.session.execute(
                _db.select(_db.func.count()).select_from(CustomFood)
            ).scalar()
            assert count == 0


class TestCustomFoodEdit:
    def test_get_edit_form_returns_200(self, client, custom_food):
        assert client.get(f'/custom-foods/{custom_food}/edit').status_code == 200

    def test_get_nonexistent_returns_404(self, client):
        assert client.get('/custom-foods/9999/edit').status_code == 404

    def test_post_update_saves_changes(self, client, custom_food, app):
        resp = client.post(f'/custom-foods/{custom_food}/update', data={
            'name': 'Renamed Oat', 'serving_description': '50g',
            **{k: '99' for k in _NUTRITION},
        })
        assert resp.status_code == 302
        with app.app_context():
            cf = _db.session.get(CustomFood, custom_food)
            assert cf.name == 'Renamed Oat'
            assert cf.calories == 99.0

    def test_post_update_nonexistent_returns_404(self, client):
        assert client.post('/custom-foods/9999/update', data={
            'name': 'x', 'serving_description': 'y', **_NUTRITION,
        }).status_code == 404


class TestCustomFoodDelete:
    def test_delete_unused_food_removes_it(self, client, custom_food, app):
        resp = client.post(f'/custom-foods/{custom_food}/delete')
        assert resp.status_code == 302
        with app.app_context():
            assert _db.session.get(CustomFood, custom_food) is None

    def test_delete_used_food_without_confirm_does_not_delete(self, client, custom_food_in_use, app):
        cf_id, _, _ = custom_food_in_use
        resp = client.post(f'/custom-foods/{cf_id}/delete')
        assert resp.status_code == 302
        with app.app_context():
            assert _db.session.get(CustomFood, cf_id) is not None

    def test_delete_used_food_with_confirm_deletes_it(self, client, custom_food_in_use, app):
        cf_id, _, _ = custom_food_in_use
        resp = client.post(f'/custom-foods/{cf_id}/delete', data={'confirm': '1'})
        assert resp.status_code == 302
        with app.app_context():
            assert _db.session.get(CustomFood, cf_id) is None

    def test_delete_nonexistent_returns_404(self, client):
        assert client.post('/custom-foods/9999/delete').status_code == 404
