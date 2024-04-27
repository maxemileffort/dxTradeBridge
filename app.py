from flask import Flask, request, jsonify
from identity import Identity  
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
# Set up rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1 per second"]
)

@app.route("/")
@limiter.limit("5 per minute")  
def home():
    return "Hello, World!"

@app.route("/check_payload", methods=['POST'])
@limiter.limit("5 per minute")  
def home():
    # Read raw text data from the request and split by comma
    raw_data = request.data.decode('utf-8')
    data_list = raw_data.strip().split(',')
    return jsonify({"message": "payload check.", "details": data_list}), 200
    

@app.route('/receive_request', methods=['POST'])
@limiter.limit("1 per second")  
def receive_request():
    # Read raw text data from the request and split by comma
    raw_data = request.data.decode('utf-8')
    data_list = raw_data.strip().split(',')
    if len(data_list) < 4:
        return jsonify({"message": "missing key trade details.", "details": raw_data}), 200

    # Parse the data into variables
    username, password, server, account_id, symbol, action = data_list[:6]
    order_side, quantity, tp, sl, trade_id = data_list[6:]

    # Convert numeric data from strings to appropriate types
    quantity = float(quantity) 
    tp = float(tp)
    sl = float(sl)
    
    # Create an instance of Identity for each request to ensure authentication
    identity = Identity(username, password, server, account_id)
    identity.login()
    
    # Determine the action to perform based on the request data
    action = action.lower()
    order_side = order_side.upper()
    try:
        if action == 'open':
            if order_side == 'BUY':
                response = identity.buy(quantity=quantity, tp=tp, sl=sl,
                                        price=None, symbol=symbol, id=trade_id)
            elif order_side == 'SELL':
                response = identity.sell(quantity=quantity, tp=tp, sl=sl,
                                         price=None, symbol=symbol, id=trade_id)
            return jsonify({"message": "Trade opened successfully", "details": response}), 200

        elif action == 'close':
            response = identity.close_trade(symbol=symbol)
            return jsonify({"message": "Trade closed successfully", "details": response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
