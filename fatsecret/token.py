import time
import requests

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