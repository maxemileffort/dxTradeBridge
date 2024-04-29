import requests
import json
import uuid
import pandas as pd

BUY = 'BUY'
SELL = 'SELL'

class Identity:
    def __init__(self, username, password, server, accountId):
        self.url_account_id = accountId.replace(':', '%3A')
        self.account_id = accountId
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
        qty_send = quantity * self.get_lot_size(symbol)
        url = f"{self.server}/dxsca-web/accounts/{self.url_account_id}/orders"
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
                        "quantity": qty_send,
                        "positionEffect": "OPEN",
                        "side": f"{order_side}",
                        "limitPrice": limit_price,
                        "tif": "GTC"
            }
        else:
            orderLeg1 = {
                        "orderCode": f"{id}-1",
                        "type": "MARKET",
                        "instrument": f"{symbol}",
                        "quantity": qty_send,
                        "positionEffect": "OPEN",
                        "side": f"{order_side}",
                        "tif": "GTC"
            }

        decimal_places = {
            'XAU' : '%.02f',
            'US500' : '%.02f',
            'XAG' : '%.03f',
            'JPY' : '%.03f'
        }

        rounding_amt = '%.05f'

        for d in decimal_places.keys():
            if d in symbol:
                rounding_amt = decimal_places[d]

        if sl and sl != 0:
            sl_send = float(rounding_amt % sl)
            orderLeg2 = {
                        "orderCode": f"{id}-2",
                        "type": "STOP",
                        "instrument": f"{symbol}",
                        "quantity": f"{0}",
                        "positionEffect": "CLOSE",
                        "side": "SELL" if order_side == 'BUY' else 'BUY',
                        "stopPrice": sl_send,
                        "tif": "GTC"
            }
        else:
            orderLeg2 = {}
        if tp and tp != 0:
            tp_send = float(rounding_amt % tp)
            orderLeg3 = {
                        "orderCode": f"{id}-3",
                        "type": "LIMIT",
                        "instrument": f"{symbol}",
                        "quantity": 0,
                        "positionEffect": "CLOSE",
                        "side": "SELL" if order_side == 'BUY' else 'BUY',
                        "limitPrice": tp_send,
                        "tif": "GTC"
            }
        else:
            orderLeg3 = {}

        orders = [orderLeg1]
        if sl != 0:
            orders.append(orderLeg2)
        if tp != 0:
            orders.append(orderLeg3)

        if len(orders) > 1:
            payload = {
                "orders": orders,
                "contingencyType": "IF-THEN"
            }
        else:
            payload = orders[0]

        print("PAYLOAD", payload)
        response = self.s.post(url, headers=headers, data=json.dumps(payload).replace(" ", ""))
        if response.status_code != 200:
            print("market order response:", response.status_code, response.text)
            return json.dumps(response)
        else:
            print("Order executed successfully!")

    def close_trade(self, symbol):
        url = f"{self.server}/dxsca-web/accounts/{self.url_account_id}/orders"
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
            return json.dumps(response)
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

    def get_lot_size(self, symbol):
        url = f'{self.server}/dxsca-web/instruments/query?symbols={symbol}'
        headers = {
            'content-type': 'application/json; charset=UTF-8',
            'Authorization': 'DXAPI '+self.authToken,
        }
        response = self.s.get(url, headers=headers)
        if response.status_code == 200:
            instr_info = json.loads(response.text)
            print('instr_info:', instr_info)
            print(float('%.05f' % instr_info['instruments'][0]['lotSize']))
            return float('%.05f' % instr_info['instruments'][0]['lotSize'])
        else:
            print("lot size response:", response.status_code, response.text)

    def get_price_increment(self, symbol):
        url = f'{self.server}/dxsca-web/instruments/query?symbols={symbol}'
        headers = {
            'content-type': 'application/json; charset=UTF-8',
            'Authorization': 'DXAPI '+self.authToken,
        }
        response = self.s.get(url, headers=headers)
        if response.status_code == 200:
            instr_info = json.loads(response.text)
            # print('instr_info:', instr_info)
            print(float('%.05f' % instr_info['instruments'][0]['priceIncrement']))
            return float('%.05f' % instr_info['instruments'][0]['priceIncrement'])
        else:
            print("lot size response:", response.status_code, response.text)

    def get_positions(self):
        url = f'{self.server}/dxsca-web/accounts/{self.url_account_id}/positions'
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
        positions = self.get_positions()['positions']
        if len(positions) == 0:
            print('no positions!')
            return ''
        print(positions)
        for p in positions:
            print(p)
            if p['symbol'] == symbol:
                return p['positionCode']
        
        return ''
    
    def buy(self, quantity, tp, sl, price, symbol, id):
        self.open_trade(BUY, quantity, tp,sl, price, symbol, id)

    def sell(self, quantity, tp,sl,price, symbol, id):
        self.open_trade(SELL, quantity, tp,sl, price, symbol, id)

    
if __name__ == "__main__":
    from dotenv import load_dotenv
    from datetime import datetime
    import time
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
    time.sleep(1)
    identity.get_positions()
    # time.sleep(1)
    # now_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    # time.sleep(1)
    # identity.buy(0.01, 20, 40, None, "LTCUSD", "LTCTEST"+now_str, )
    # time.sleep(1)
    # identity.close_trade("LTCUSD")
    # time.sleep(1)
    # identity.buy(0.01, 20, 40, None, "BTCUSD", "BTCTEST"+now_str)
    # time.sleep(1)
    # identity.close_trade("BTCUSD")
    # time.sleep(1)
    # identity.buy(0.01, 0, 0, None, "EURUSD", "EUTEST"+now_str)
    # time.sleep(1)
    # identity.close_trade("EURUSD")