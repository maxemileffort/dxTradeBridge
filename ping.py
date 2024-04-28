import requests

url = 'https://dxtradebridge.onrender.com'

r = requests.get(url)
r.status_code, r.text