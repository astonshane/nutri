import pytest
from sqlalchemy.pool import StaticPool

from nutri import create_app, db as _db
from nutri.models import Dish, Ingredient


@pytest.fixture(scope="session")
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
        "SECRET_KEY": "test-secret-key",
        "FATSECRET_CLIENT_ID": "fake-id",
        "FATSECRET_CLIENT_SECRET": "fake-secret",
    })
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def dish(app):
    with app.app_context():
        d = Dish(title="Pasta", portions=2)
        _db.session.add(d)
        _db.session.commit()
        return d.id


@pytest.fixture
def dish_with_ingredient(app):
    with app.app_context():
        d = Dish(title="Pasta", portions=2)
        _db.session.add(d)
        _db.session.flush()
        ing = Ingredient(
            food_id=100,
            serving_id=200,
            quantity=1.5,
            dish_id=d.id,
            food_name="Chicken",
            food_url=None,
            serving_description="100g",
            calories=165.0,
            fat=3.6,
            sodium=74.0,
            carbohydrate=0.0,
            fiber=0.0,
            protein=31.0,
        )
        _db.session.add(ing)
        _db.session.commit()
        return d.id, ing.id
