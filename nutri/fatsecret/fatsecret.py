import requests
from .food import Food
from .token import Token


class Fatsecret:
    def __init__(self):
        pass

    def setToken(self, client_id, client_secret):
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
        # print(results_json)
        return Food(results_json['food'])
