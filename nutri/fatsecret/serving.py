class Serving:
    def __init__(self, body):
        self.id = body.get('serving_id')
        self.description = body.get('serving_description')
        self.measurement_description = body.get('measurement_description')
        self.number_of_units = body.get('number_of_units', 0)
        self.calories = float(body.get('calories', 0))
        self.carbohydrate = float(body.get('carbohydrate', 0))
        self.protein = float(body.get('protein', 0))
        self.fat = float(body.get('fat', 0))
        self.cholesterol = float(body.get('cholesterol', 0))
        self.sodium = float(body.get('sodium', 0))
        self.fiber = float(body.get('fiber', 0))
        self.sugar = float(body.get('sugar', 0))