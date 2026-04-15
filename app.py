from flask import Flask, jsonify, request
import yfinance as yf

app = Flask(__name__)

TIMEFRAMES = {
    "1d": "1d",
    "1w": "7d",
    "1m": "1mo",
    "3m": "3mo",
    "1y": "1y"
}

@app.route("/")
def home():
    return "FinanceGPT API Running 🚀"

@app.route("/stock/<ticker>")
def get_stock(ticker):
    timeframe = request.args.get("range", "1m")
    period = TIMEFRAMES.get(timeframe, "1mo")

    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)

    data = [
        {"date": str(i.date()), "close": float(r["Close"])}
        for i, r in hist.iterrows()
    ]

    return jsonify({"ticker": ticker, "data": data})