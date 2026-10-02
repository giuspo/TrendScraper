import requests

API_KEY = "7986c654ac1aded6bb379b04a2ff4d21dd55ba45b10689d9a60e5b1cc38d31d8"
url = f"https://serpapi.com/account.json?api_key={API_KEY}"
resp = requests.get(url)
print(resp.json())