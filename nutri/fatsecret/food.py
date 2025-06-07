from fatsecret.serving import Serving

class Food:
    def __init__(self, body):
        self.id = body.get('food_id')
        self.name = body.get('food_name')
        self.brand = body.get('food_type')
        self.url = body.get('food_url')
        if 'brand_name' in body:
            self.brand = body['brand_name']
        self.servings = [Serving(x) for x in body.get('servings', {}).get('serving', [])]

    def __repr__(self):
        return f"Food(id={self.id}, name={self.name}, brand={self.brand})"