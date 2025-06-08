from . import db, fs

class Dish(db.Model):
    __tablename__ = "dishes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), index=True, unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    ingredients = db.relationship('Ingredient', back_populates='dish')

    def __repr__(self):
        return f"<Dish id={self.id}, title={self.title}>"
    
    def nutrition(self):
        total_nutrition = {
            'calories': 0,
            'fat': 0,
            'sodium': 0,
            'carbohydrates': 0,
            'fiber': 0,
            'protein': 0
        }
        for ingredient in self.ingredients:
            ing_nutrition = ingredient.nutrition()
            for key in total_nutrition:
                total_nutrition[key] += ing_nutrition[key]
        return total_nutrition
    
class Ingredient(db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, nullable=False)
    serving_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    dish = db.relationship('Dish', back_populates='ingredients')

    _food = None
    _serving = None
    _nutrition = None
    _nutrition_per_serving = None

    def __repr__(self):
        return f"<Ingredient id={self.id}, food_id={self.food_id}>"
    
    def food(self):
        if self._food is None:
            _food = fs.food(self.food_id)
        return _food
    
    def serving(self):
        if self._serving is None:
            _serving = self.food().serving(self.serving_id)
        return _serving
    
    def nutrition(self, per_serving=False):
        if per_serving and self._nutrition_per_serving is not None:
            return self._nutrition_per_serving
        
        if not per_serving and self._nutrition is not None:
            return self._nutrition

        s = self.serving()
        mult = 1 if per_serving else self.quantity
        n = {
            'calories': s.calories * mult,
            'fat': s.fat * mult,
            'sodium': s.sugar * mult,
            'carbohydrates': s.carbohydrate * mult,
            'fiber': s.fiber * mult,
            'protein': s.protein * mult
        }

        if per_serving:
            self._nutrition_per_serving = n
        else:
            self._nutrition = n

        return n
