import requests

def ping():

    url = 'https://dxtradebridge.onrender.com'

    r = requests.get(url)
    print(r.status_code, r.text)

if __name__ == "__main__":
    ping()