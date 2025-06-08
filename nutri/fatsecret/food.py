from .serving import Serving

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
    
    def serving(self, serving_id):
        serving_id = str(serving_id)
        print(f"Searching for serving with ID: {serving_id} in food {self.id}")
        for serving in self.servings:
            print(type(serving_id), serving_id, type(serving.id), serving.id)
            if serving.id == serving_id:
                print(f"Found serving: {serving}")
                return serving
        return None