# main.py
# This is the backend web server for the AlgoTradeBolt interface.
# It uses Flask to create an API that the frontend can call to get live data.

# --- How to use ---
# 1. Make sure you have 'config.py' with your API keys in the same directory.
#
# 2. Install the required libraries:
#    pip install Flask flask-cors ccxt termcolor
#
# 3. Run this script from your terminal:
#    python main.py
#
# 4. The server will start on port 5000.
# --------------------

from flask import Flask, jsonify
from flask_cors import CORS
from termcolor import colored
import ccxt
import sys
import datetime

# --- Configuration and Initialization ---
app = Flask(__name__)
CORS(app)

try:
    import config
except ImportError:
    print(colored("[ERROR] Configuration file 'config.py' not found.", 'red'))
    print(colored("Please create 'config.py' and add your API credentials.", 'yellow'))
    sys.exit(1)

# --- Helper Function for Exchange Connection ---

def get_exchange_data(exchange_id, api_credentials):
    """
    Connects to a single exchange and fetches its non-zero balances,
    including USD prices and values for each asset.
    """
    exchange_name = exchange_id.capitalize()
    print(colored(f"\n----- [CONNECTING TO: {exchange_name}] -----", 'yellow'))
    
    try:
        # Initialize CCXT exchange class and fetch balance
        print(f"[{datetime.datetime.now()}] Initializing and fetching balance for {exchange_name}...")
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class(api_credentials)
        balance = exchange.fetch_balance()
        
        print(colored(f"✅ [{datetime.datetime.now()}] {exchange_name}: Connection successful.", 'green'))
        
        non_zero_balances = {k: v for k, v in balance['total'].items() if v > 0}
        
        assets_with_details = {}
        total_portfolio_value_usd = 0
        
        print(f"[{datetime.datetime.now()}] Fetching market prices for {len(non_zero_balances)} asset(s)...")

        for currency, total in non_zero_balances.items():
            details = {'total': total, 'price_usd': 1.0, 'value_usd': total}
            
            # For non-stablecoins, try to fetch the price against USDT
            if currency not in ['USDT', 'USDC', 'BUSD', 'TUSD', 'DAI']:
                try:
                    ticker = exchange.fetch_ticker(f'{currency}/USDT')
                    details['price_usd'] = ticker['last']
                    details['value_usd'] = total * ticker['last']
                except Exception:
                    # If direct USDT pair doesn't exist, can't determine price
                    details['price_usd'] = 0
                    details['value_usd'] = 0
                    print(colored(f"Could not fetch USDT price for {currency} on {exchange_name}.", 'magenta'))

            assets_with_details[currency] = details
            total_portfolio_value_usd += details['value_usd']

        print(colored(f"✅ [{datetime.datetime.now()}] {exchange_name}: Data processing complete.", 'green'))
        
        return {
            "assets": assets_with_details,
            "total_value_usd": total_portfolio_value_usd
        }

    except ccxt.AuthenticationError as e:
        error_msg = f"Authentication Error with {exchange_name}. Check API credentials in config.py."
        print(colored(f"❌ [{datetime.datetime.now()}] {error_msg}", 'red'))
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred with {exchange_name}."
        print(colored(f"❌ [{datetime.datetime.now()}] {error_msg}\n   Details: {e}", 'red'))
        return {"error": error_msg}

# --- API Endpoints ---

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "ok", "message": "Backend is running."})

@app.route('/api/dashboard_data', methods=['GET'])
def get_dashboard_data():
    """
    Main endpoint to fetch all data required for the dashboard.
    For now, it treats each exchange as a single portfolio.
    """
    print("\n" + colored("="*50, 'blue'))
    print(colored(f"[{datetime.datetime.now()}] Received request for /api/dashboard_data", 'cyan'))
    print(colored("="*50, 'blue'))
    
    dashboard_data = {}

    # Fetch from Binance if keys are present
    if hasattr(config, 'BINANCE_API_KEY') and config.BINANCE_API_KEY and 'YOUR_BINANCE_API_KEY' not in config.BINANCE_API_KEY:
        binance_creds = {'apiKey': config.BINANCE_API_KEY, 'secret': config.BINANCE_API_SECRET}
        dashboard_data['Binance - Main Account'] = get_exchange_data('binance', binance_creds)
    
    # Fetch from KuCoin if keys are present
    if hasattr(config, 'KUCOIN_API_KEY') and config.KUCOIN_API_KEY and 'YOUR_KUCOIN_API_KEY' not in config.KUCOIN_API_KEY:
        kucoin_creds = {'apiKey': config.KUCOIN_API_KEY, 'secret': config.KUCOIN_API_SECRET, 'password': config.KUCOIN_API_PASSPHRASE}
        dashboard_data['KuCoin - Main Account'] = get_exchange_data('kucoin', kucoin_creds)

    print("\n" + colored("="*50, 'blue'))
    print(colored(f"[{datetime.datetime.now()}] Finished processing dashboard data request.", 'cyan'))
    print(colored("="*50, 'blue'))
    
    return jsonify(dashboard_data)

# --- Main execution block ---

if __name__ == '__main__':
    print(colored("="*50, 'magenta'))
    print(colored("   Starting AlgoTradeBolt Backend Server", 'magenta'))
    print(colored("="*50, 'magenta'))
    app.run(host='0.0.0.0', port=5000, debug=True)
