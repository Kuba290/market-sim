from flask import Flask, render_template, request, redirect, url_for
import yfinance as yf
import sqlite3

app = Flask(__name__)

BASE_CURRENCY = "USD"

def db_init():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT UNIQUE NOT NULL, cash FLOAT NOT NULL DEFAULT 10000)")
    cursor.execute("INSERT OR IGNORE INTO user (id, login, cash) VALUES (?, ?, ?)", (0, "user", 10000))
    cursor.execute("CREATE TABLE IF NOT EXISTS portfolio (symbol TEXT PRIMARY KEY, quantity INTEGER)")
    conn.commit()
    conn.close()

def get_portfolio():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio")
    data = cursor.fetchall()
    conn.close()
    return data

def get_balance():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT cash FROM user WHERE id=0")
    data = cursor.fetchone()
    conn.close()
    return data[0]

def update_balance(amount):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE user SET cash = cash + ? WHERE id=0", (amount,))
    conn.commit()
    conn.close()

def fetch_stock_data(ticker_symbol):
    try:
        ticker_symbol = ticker_symbol.upper().strip()
        stock = yf.Ticker(ticker_symbol)
        history = stock.history(period="1d")
        
        if history.empty:
            return None
            
        price = history['Close'].iloc[-1]
        info = stock.info
        
        name = info.get('longName') or info.get('shortName') or ticker_symbol
        currency = info.get('currency', 'USD')

        rate = get_exchange_rate(currency, BASE_CURRENCY) if currency != BASE_CURRENCY else 1.0
        price_in_USD = price * rate
        
        return {"ticker": ticker_symbol, "price": price, "name": name, "currency": currency, "price_in_USD": price_in_USD}
    except Exception:
        return None

def get_exchange_rate(from_currency, to_currency='USD'):
    if from_currency == to_currency:
        return 1.0

    pair = f'{from_currency}{to_currency}=X' # USDEUR=X
    ticker_data = yf.Ticker(pair)
    history = ticker_data.history(period='1d')

    return history['Close'].iloc[-1]
  
@app.route("/")
def index():
    ticker = request.args.get("ticker", "").strip()
    stock_info = None
    
    if ticker:
        stock_info = fetch_stock_data(ticker)

    balance = get_balance()
    user_data = get_portfolio()
    total_value = balance

    portfolio_list = []

    for row in user_data:
        symbol = row[0]
        quantity = row[1]
        
        stock_data = fetch_stock_data(symbol)
        current_price = stock_data["price"]
        currency = stock_data.get("currency", "USD")
        
        rate = get_exchange_rate(currency, BASE_CURRENCY) if currency != BASE_CURRENCY else 1.0
        
        price_in_USD = current_price * rate
        item_value = quantity * price_in_USD
        
        total_value += item_value

        portfolio_list.append({
            "symbol": symbol,
            "quantity": quantity,
            "current_price": price_in_USD,
            "total_item_value": item_value,
        })

    return render_template('index.html', cash=balance, portfolio=portfolio_list, total_portfolio_value=total_value, active_ticker=ticker, stock_info=stock_info)

@app.route("/trade", methods=["POST"])
def trade():
    ticker = request.form.get("ticker")
    action = request.form.get("action")
    try:
        amount = int(request.form.get("amount", 1))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        return redirect(url_for("index"))

    stock_data = fetch_stock_data(ticker)
    if not stock_data:
        return redirect(url_for("index"))

    price = stock_data["price"]
    currency = stock_data.get("currency", "USD")

    rate = get_exchange_rate(currency, BASE_CURRENCY) if currency != BASE_CURRENCY else 1.0

    price_in_USD = price * rate
    total_cost = price_in_USD * amount 

    balance = get_balance()
    user_data = get_portfolio()

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    if action == "buy":
        if balance >= total_cost:
            update_balance(-total_cost)
            cursor.execute("INSERT INTO portfolio (symbol, quantity) VALUES (?, ?) ON CONFLICT(symbol) DO UPDATE SET quantity = quantity + ?", (ticker, amount, amount))
            conn.commit()

    elif action == "sell":
        found_item = None
        for row in user_data:
            if row[0] == ticker: 
                found_item = row
                break

        if found_item and found_item[1] >= amount:
            current_quantity = found_item[1]
            update_balance(total_cost)
            
            if current_quantity == amount:
                cursor.execute("DELETE FROM portfolio WHERE symbol = ?", (ticker,))
            else:
                cursor.execute("UPDATE portfolio SET quantity = quantity - ? WHERE symbol = ?", (amount, ticker))   
            conn.commit()

    conn.close()
    return redirect(url_for("index", ticker=ticker))

if __name__ == "__main__":
    db_init()
    app.run(host="0.0.0.0", port=2500, debug=False)