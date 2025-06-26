# main.py
# This is the backend web server for the AlgoTradeBolt interface.
# It uses Flask to create an API that the frontend can call to get live data.

# --- How to use ---
# 1. Make sure you have 'config.py' with your API keys in the same directory.
#
# 2. Install the required libraries:
#    pip install Flask flask-cors ccxt
#
# 3. Run this script from your terminal:
#    python main.py
#
# 4. The server will start, and your web interface can now fetch data from it.
# --------------------

from flask import Flask, jsonify
from flask_cors import CORS
import ccxt
import sys

# --- Configuration and Initialization ---

# Initialize the Flask app
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) to allow the frontend
# to make requests to this server.
CORS(app)

# Attempt to import the API key configuration
try:
    import config
except ImportError:
    print("[ERROR] Configuration file 'config.py' not found.")
    print("Please create 'config.py' and add your API credentials before running the server.")
    sys.exit(1)


# --- Helper Function for Exchange Connection ---

def get_exchange_balances(exchange_id, api_credentials):
    """
    Connects to a single exchange and fetches its non-zero balances.
    Returns a dictionary of balances or an error message.
    """
    exchange_name = exchange_id.capitalize()
    print(f"Attempting to connect to {exchange_name}...")
    
    try:
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class(api_credentials)
        balance = exchange.fetch_balance()
        
        non_zero_balances = {
            currency: total
            for currency, total in balance['total'].items()
            if total > 0
        }
        print(f"Successfully fetched balances from {exchange_name}.")
        return non_zero_balances

    except ccxt.AuthenticationError as e:
        error_msg = f"Authentication Error with {exchange_name}: {e}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred with {exchange_name}: {e}"
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}


# --- API Endpoints ---
# These are the URLs that the frontend will call to get data.

@app.route('/api/status', methods=['GET'])
def get_status():
    """A simple endpoint to check if the backend server is running."""
    return jsonify({"status": "ok", "message": "Backend is running."})

@app.route('/api/balances', methods=['GET'])
def get_all_balances():
    """
    The main endpoint to fetch balances from all configured exchanges.
    The frontend will call this URL.
    """
    print("\nReceived request for /api/balances")
    all_balances = {}

    # Fetch from Binance if keys are present in config
    if hasattr(config, 'BINANCE_API_KEY') and config.BINANCE_API_KEY != 'YOUR_BINANCE_API_KEY':
        binance_creds = {'apiKey': config.BINANCE_API_KEY, 'secret': config.BINANCE_API_SECRET}
        all_balances['binance'] = get_exchange_balances('binance', binance_creds)
    
    # Fetch from KuCoin if keys are present in config
    if hasattr(config, 'KUCOIN_API_KEY') and config.KUCOIN_API_KEY != 'YOUR_KUCOIN_API_KEY':
        kucoin_creds = {
            'apiKey': config.KUCOIN_API_KEY,
            'secret': config.KUCOIN_API_SECRET,
            'password': config.KUCOIN_API_PASSPHRASE
        }
        all_balances['kucoin'] = get_exchange_balances('kucoin', kucoin_creds)

    # Return the combined data to the frontend as JSON
    return jsonify(all_balances)


# --- Main execution block ---

if __name__ == '__main__':
    # Starts the Flask web server.
    # It will be accessible at http://127.0.0.1:5000
    # The `debug=True` argument enables auto-reloading when you save the file.
    print("Starting AlgoTradeBolt backend server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
