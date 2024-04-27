from flask import Flask, request, jsonify
from identity import Identity  # Assuming Identity class is in a separate file called identity.py

app = Flask(__name__)

@app.route('/receive_request', methods=['POST'])
def receive_request():
    data = request.json
    # Create an instance of Identity for each request to ensure authentication
    identity = Identity(data['username'], data['password'], "", data["accountId"])
    identity.login()
    
    # Determine the action to perform based on the request data
    if data['action'].lower() == 'open':
        try:
            if data['order_side'].upper() == 'BUY':
                identity.buy(quantity=data['quantity'], tp=data['tp'], sl=data['sl'],
                             price=data['price'], symbol=data['symbol'], instrument_id=data['instrument_id'])
            elif data['order_side'].upper() == 'SELL':
                identity.sell(quantity=data['quantity'], tp=data['tp'], sl=data['sl'],
                              price=data['price'], symbol=data['symbol'], instrument_id=data['instrument_id'])
            return jsonify({"message": "Trade opened successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    elif data['action'].lower() == 'close':
        try:
            identity.close_trade(position_id=data['position_id'], quantity=data['quantity'],
                                 price=data['price'], symbol=data['symbol'], instrument_id=data['instrument_id'])
            return jsonify({"message": "Trade closed successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
