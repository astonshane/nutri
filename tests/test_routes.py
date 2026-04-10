"""Route integration tests using the Flask test client."""
from unittest.mock import MagicMock, patch

import pytest

from nutri import db as _db
from nutri.models import Dish, Ingredient


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
