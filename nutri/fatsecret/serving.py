from ..helpers import BaseModel, static_nutrition_info

class Serving:
    def __init__(self, body):
        self.id = body.get('serving_id')
        self.description = body.get('serving_description')
        self.measurement_description = body.get('measurement_description')
        self.number_of_units = body.get('number_of_units', 0)

        self.nutrition_info = {}
        for key in static_nutrition_info.keys():
            self.nutrition_info[key] = float(body.get(key, 0))
