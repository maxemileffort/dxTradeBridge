import requests
import json
import uuid
import pandas as pd

BUY = 'BUY'
SELL = 'SELL'

class Identity:
    def __init__(self, username, password, server, accountId):
        self.account_id = accountId.replace(':', '%3A')
        self.username = username
        self.fullUsername = ""
        self.password = password
        self.server = server
        self.authToken = ""
        self.s = requests.Session()

    def login(self):
        url = f"{self.server}/dxsca-web/login"
        payload = json.dumps({
            "username": self.username,
            "password": self.password,
            "domain": "default"
        })
        headers = {
            'content-type': 'application/json',
        }
        response = self.s.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            print(json.loads(response.text))
            self.authToken = json.loads(response.text)['sessionToken']
            
            print("Logged in!")
        else:
            print("Login failed with status code:", response.status_code)


    def open_trade(self, order_side, quantity, tp, sl, limit_price, symbol, id):
        url = f"{self.server}/dxsca-web/accounts/{self.account_id}/orders"
        headers = {
            'content-type': 'application/json; charset=UTF-8',
            'Authorization': 'DXAPI '+self.authToken,
        }
        # order_base_id = uuid.uuid1()
        if limit_price and limit_price != 0:
            orderLeg1 = {
                        "orderCode": f"{id}-1",
                        "type": "LIMIT",
                        "instrument": f"{symbol}",
                        "quantity": f"{quantity / self.get_price_increment(symbol)}",
                        "positionEffect": "OPEN",
                        "side": f"{order_side}",
                        "limitPrice": f"{limit_price}",
                        "tif": "GTC"
            }
        else:
            orderLeg1 = {
                        "orderCode": f"{id}-1",
                        "type": "MARKET",
                        "instrument": f"{symbol}",
                        "quantity": f"{quantity / self.get_price_increment(symbol)}",
                        "positionEffect": "OPEN",
                        "side": f"{order_side}",
                        "tif": "GTC"
            }
        orderLeg2 = {
                    "orderCode": f"{id}-2",
                    "type": "STOP",
                    "instrument": f"{symbol}",
                    "quantity": "0",
                    "positionEffect": "CLOSE",
                    "side": "SELL" if order_side == 'BUY' else 'BUY',
                    "stopPrice": f"{sl}",
                    "tif": "GTC"
        }
        orderLeg3 = {
                    "orderCode": f"{id}-3",
                    "type": "LIMIT",
                    "instrument": f"{symbol}",
                    "quantity": "0",
                    "positionEffect": "CLOSE",
                    "side": "SELL" if order_side == 'BUY' else 'BUY',
                    "limitPrice": f"{tp}",
                    "tif": "GTC"
        }

        orders = [orderLeg1]
        if sl != 0:
            orders.append(orderLeg2)
        if tp != 0:
            orders.append(orderLeg3)

        payload = {
            "orders": orders,
            "contingencyType": "IF-THEN"
        }
        print("PAYLOAD", payload)
        response = self.s.post(url, headers=headers, data=json.dumps(payload).replace(" ", ""))
        if response.status_code != 200:
            print("market order response:", response.status_code, response.text)
        else:
            print("Order executed successfully!")

    def close_trade(self, symbol):
        url = f"{self.server}/dxsca-web/accounts/{self.account_id}/orders"
        headers = {
            'content-type': 'application/json; charset=UTF-8',
            'Authorization': 'DXAPI '+self.authToken,
        }

        payload = {
            "legs": [{
                "instrument": symbol,
                "positionCode": self.get_position_id(symbol),
                "positionEffect": "CLOSE",
                "ratioQuantity": 1
            }],
            "orderType": "MARKET",
            "timeInForce": "GTC"
        }

        print("PAYLOAD", payload)

        response = self.s.post(url, headers=headers, data=json.dumps(payload).replace(" ", ""))
        if response.status_code != 200:
            print("market order response:", response.status_code, response.text)
        else:
            print("Order executed successfully!")

    def list_instruments(self):
        url = f'{self.server}/dxsca-web/instruments/query?symbols=*'
        headers = {
            'content-type': 'application/json; charset=UTF-8',
            'Authorization': 'DXAPI '+self.authToken,
        }
        response = self.s.get(url, headers=headers)
        if response.status_code == 200:
            print(json.loads(response.text))
        else:
            print("list instruments response:", response.status_code, response.text)

    def get_price_increment(self, symbol):
        url = f'{self.server}/dxsca-web/instruments/query?symbols={symbol}'
        headers = {
            'content-type': 'application/json; charset=UTF-8',
            'Authorization': 'DXAPI '+self.authToken,
        }
        response = self.s.get(url, headers=headers)
        if response.status_code == 200:
            instr_info = json.loads(response.text)
            print(float('%.05f' % instr_info['instruments'][0]['priceIncrement']))
            return float('%.05f' % instr_info['instruments'][0]['priceIncrement'])
        else:
            print("list instruments response:", response.status_code, response.text)

    def get_positions(self):
        url = f'{self.server}/dxsca-web/accounts/{self.account_id}/positions'
        headers = {
            'content-type': 'application/json; charset=UTF-8',
            'Authorization': 'DXAPI '+self.authToken,
        }
        response = self.s.get(url, headers=headers)
        if response.status_code == 200:
            print(json.loads(response.text))
            return (json.loads(response.text))
        else:
            print("positions response:", response.status_code, response.text)

    def get_position_id(self, symbol):
        positions = self.get_positions()

        for p in positions:
            if p['symbol'] == symbol:
                return p['positionCode']
        
        return ''

    def buy(self, quantity, tp, sl, price, symbol):
        self.open_trade(BUY, quantity, tp,sl, price, symbol)

    def sell(self, quantity, tp,sl,price, symbol):
        self.open_trade(SELL, quantity, tp,sl, price, symbol)

    
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    # Load environment variables
    load_dotenv()

    # Access variables securely
    username = os.getenv('DX_USERNAME')
    password = os.getenv('DX_PASS')
    server = os.getenv('DX_SERVER')
    accountId = os.getenv('DX_ACCOUNT')

    identity = Identity(username, password, server, accountId)
    identity.login()
    # identity.get_price_increment('BTCUSD')
    # identity.get_positions()
    identity.buy(0.01, 0, 0, None, "BTCUSD")
    identity.close_trade("BTCUSD")