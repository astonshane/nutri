from . import db, fs
from .helpers import BaseModel, static_nutrition_info

class Dish(BaseModel, db.Model):
    __tablename__ = "dishes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), index=True, unique=True, nullable=False)
    description = db.Column(db.Text)
    portions = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    ingredients = db.relationship('Ingredient', back_populates='dish', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Dish id={self.id}, title={self.title}>"
    
    def nutrition(self):
        total = {key: 0 for key in static_nutrition_info.keys()}
        for ingredient in self.ingredients:
            ing_nutrition = ingredient.nutrition()
            for key in total:
                total[key] += ing_nutrition[key]
        return total

    def nutrition_per_portion(self):
        total = self.nutrition()
        portions = self.portions or 1
        return {key: val / portions for key, val in total.items()}
    
class Ingredient(BaseModel, db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, nullable=False)
    serving_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    food_name = db.Column(db.String(255))
    food_url = db.Column(db.String(512))
    serving_description = db.Column(db.String(255))
    calories = db.Column(db.Float)
    fat = db.Column(db.Float)
    sodium = db.Column(db.Float)
    carbohydrate = db.Column(db.Float)
    fiber = db.Column(db.Float)
    protein = db.Column(db.Float)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    dish = db.relationship('Dish', back_populates='ingredients')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._food = None
        self._serving = None

    def __repr__(self):
        return f"<Ingredient id={self.id}, food_id={self.food_id}>"

    def food(self):
        if self._food is None:
            self._food = fs.food(self.food_id)
        return self._food

    def serving(self):
        if self._serving is None:
            self._serving = self.food().serving(self.serving_id)
        return self._serving

    def nutrition(self):
        return {key: (getattr(self, key) or 0) * self.quantity for key in static_nutrition_info.keys()}
