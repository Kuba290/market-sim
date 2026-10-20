# Market Sim

Flask-based stock trading simulator that allow user to trade global assets, track their portfolio value in real-time, and handle currency conversions. Powered by Python, SQLite, and Yahoo Finance ([`yfinance`](https://pypi.org/project/yfinance/)).

---

## Features

* **Database**: utilizes SQLite to store and update user assets.
* **Real-time market data**: fetches up-to-date stock prices and asset details dynamically via `yfinance`.
* **Multi-currency support**: automatically normalizes all portfolio valuations and transaction costs to USD, handling foreign currencies with live exchange rate lookups (`{Currency}USD=X`).
* **Asset selection**: includes a built-in search datalist featuring major international stocks.
* **Dashboard UI with dark/light theme**: switching based on system preferences.

---

## Tech specs

* **Backend**: Python, Flask.
* **Database**: SQLite (`data.db` automatically created).
* **Financial data**: `yfinance`.
* **Frontend**: HTML.

---

## Installation & Running

1. Clone the repository or download the project files.

2. **Install dependencies:**
make sure you have Python installed, then install the required libraries:
   ```bash
   pip install flask yfinance
   ```

3. **Run app**:
    ```bash
    python app.py
    ```