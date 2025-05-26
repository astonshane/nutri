import requests
import time

class Token:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

        self.access_token = None
        self.expires_in = 0
        self.expires_at = time.time()

    def get(self):
        if self.access_token is None or time.time() >= self.expires_at:
            self.refresh()
        return self.access_token
    
    def refresh(self):
        data = {
            'grant_type': 'client_credentials',
            'scope': 'basic',
        }
        resp = requests.post("https://oauth.fatsecret.com/connect/token", auth=(self.client_id, self.client_secret), data=data)
        if resp.status_code == 200:
            body = resp.json()
            self.access_token = body.get('access_token')
            self.expires_in = int(body.get('expires_in', 0))
            self.expires_at = time.time() + self.expires_in
        else:
            print("Failed to refresh token:", resp.status_code, resp.text)

class Serving:
    def __init__(self, body):
        self.id = body.get('serving_id')
        self.description = body.get('serving_description')
        self.metric_serving_amount = body.get('metric_serving_amount')
        self.metric_serving_unit = body.get('metric_serving_unit')
        self.number_of_units = body.get('number_of_units')
        self.calories = body.get('calories')
        self.carbohydrate = body.get('carbohydrate')
        self.protein = body.get('protein')
        self.fat = body.get('fat')
        self.cholesterol = body.get('cholesterol')
        self.sodium = body.get('sodium')
        self.fiber = body.get('fiber')
        self.sugar = body.get('sugar')


class Food:
    def __init__(self, body):
        self.id = body.get('food_id')
        self.name = body.get('food_name')
        self.type = body.get('food_type')
        self.url = body.get('food_url')
        self.servings = [Serving(x) for x in body.get('servings', {}).get('serving', [])]

    def __repr__(self):
        return f"Food(id={self.id}, name={self.name}, type={self.type})"


class Fatsecret:
    def __init__(self, client_id, client_secret):
        self.token = Token(client_id, client_secret)

    def request(self, path, params):
        base_url = "https://platform.fatsecret.com/rest"
        url = f"{base_url}{path}"
        token = self.token.get()

        # Content-Type: application/json
        # Header: Authorization: Bearer <Access Token>
        resp = requests.get(url, headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }, params=params)

        return resp.json()

        # if resp.status_code == 200:
        #     body = resp.json()
        #     if body.get('error'):
        #         print("Error in response:", body['error'])
        #         return None
        # else:
        #     return None
        
    def search(self, search_expression, max_results=10, page_number=0):
        path = "/foods/search/v1"
        params = {
            'search_expression': search_expression,
            'max_results': max_results,
            'format': 'json',
            'page_number': page_number
        }
        results_json = self.request(path, params)
        results = [Food(item) for item in results_json['foods']['food']]
        return results
    
    def food(self, food_id):
        path = "/food/v4"
        params = {
            'food_id': food_id,
            'format': 'json'
        }
        results_json = self.request(path, params)
        print(results_json)
        return Food(results_json['food'])
