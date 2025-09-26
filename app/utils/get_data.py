import requests
class Data:
    def __init__(self, url: str, cookies: dict):
        self.url = url
        self.cookies = cookies

    def get_data(self):
        response = requests.get(self.url, cookies=self.cookies)
        response.raise_for_status() 
        return response.json()       
