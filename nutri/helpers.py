static_nutrition_info = {
    'calories': {
        'label': 'Calories',
        'unit': 'kcal'
    },
    'fat': {
        'label': 'Fat',
        'unit': 'g'
    },
    'sodium': {
        'label': 'Sodium',
        'unit': 'mg'
    },
    'carbohydrate': {
        'label': 'Carbohydrates',
        'unit': 'g'
    },
    'fiber': {
        'label': 'Fiber',
        'unit': 'g'
    },
    'protein': {
        'label': 'Protein',
        'unit': 'g'
    }
}

class BaseModel:
    __abstract__ = True

    def static_nutrition_info(self):
        return static_nutrition_info
    
    def static_nutrition_keys(self):
        return list(static_nutrition_info.keys())
    
    def static_nutrition_label(self, key, withUnit=True):
        if key not in static_nutrition_info:
            return key
        label = static_nutrition_info[key]['label']
        if withUnit:
            label += f" ({static_nutrition_info[key]['unit']})"
        return label