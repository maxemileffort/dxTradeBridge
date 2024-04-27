from flask import Flask, request, jsonify
from identity import Identity  # Assuming Identity class is in a separate file called identity.py
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
@limiter.limit("5 per minute")  # Specific limit for this endpoint
def home():
    return "Hello, World!"

@app.route('/receive_request', methods=['POST'])
@limiter.limit("1 per second")  
def receive_request():
    # Read raw text data from the request and split by comma
    raw_data = request.data.decode('utf-8')
    data_list = raw_data.strip().split(',')

    # Parse the data into variables
    username, password, server, account_id, symbol, action, order_side, quantity, tp, sl, trade_id = data_list

    # Convert numeric data from strings to appropriate types
    quantity = int(quantity) 
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
