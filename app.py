from flask import Flask, render_template, request, redirect, url_for
import yfinance as yf

app = Flask(__name__)

user_data = {
    "cash": 10000.0,
    "portfolio": {}  
}

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
        
        return {"ticker": ticker_symbol, "price": price, "name": name, "currency": currency}
    except Exception:
        return None

@app.route("/")
def index():
    ticker = request.args.get("ticker", "").strip()
    stock_info = None
    
    if ticker:
        stock_info = fetch_stock_data(ticker)

    total_value = user_data["cash"]
    for symbol, asset in user_data["portfolio"].items():
        data = fetch_stock_data(symbol)
        current_price = data["price"] if data else 0.0
        asset["current_price"] = current_price
        total_value += asset["shares"] * current_price

    return render_template('index.html', cash=user_data["cash"], portfolio=user_data["portfolio"], total_portfolio_value=total_value, active_ticker=ticker, stock_info=stock_info)

@app.route("/trade", methods=["POST"])
def trade():
    ticker = request.form.get("ticker")
    action = request.form.get("action")
    amount = int(request.form.get("amount", 1))

    stock_data = fetch_stock_data(ticker)
    if not stock_data:
        return redirect(url_for("index"))

    price = stock_data["price"]
    total_cost = price * amount

    if action == "buy":
        if user_data["cash"] >= total_cost:
            user_data["cash"] -= total_cost
            if ticker in user_data["portfolio"]:
                user_data["portfolio"][ticker]["shares"] += amount
            else:
                user_data["portfolio"][ticker] = {"shares": amount}

    elif action == "sell":
        if ticker in user_data["portfolio"] and user_data["portfolio"][ticker]["shares"] >= amount:
            user_data["cash"] += total_cost
            user_data["portfolio"][ticker]["shares"] -= amount
            if user_data["portfolio"][ticker]["shares"] == 0:
                del user_data["portfolio"][ticker]

    return redirect(url_for("index", ticker=ticker))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2500, debug=True)