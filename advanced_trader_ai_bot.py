# advanced_trader_ai_bot.py
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import os

# Optional: AI assistant
try:
    from openai import OpenAI
    client = OpenAI(api_key="YOUR_OPENAI_API_KEY")
except:
    client = None

# Optional: Telegram alerts
# pip install python-telegram-bot
try:
    from telegram import Bot
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
except:
    bot = None

# -------------------------
# Step 1: Setup
# -------------------------
symbols = ["ES=F", "NQ=F"]  # Add more symbols if you want
interval = "5m"
lookback_days = "30d"

# Ensure data folder exists
if not os.path.exists("data"):
    os.makedirs("data")

# Ensure trade journal exists
journal_file = "trade_journal.csv"
if not os.path.exists(journal_file):
    with open(journal_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Symbol", "Trade_Time", "Price", "Signal", "Result"])

# -------------------------
# Step 2: Download and Process Data
# -------------------------
all_signals = pd.DataFrame()

for symbol in symbols:
    data = yf.download(symbol, period=lookback_days, interval=interval)
    data.reset_index(inplace=True)
    data['Prev_Close'] = data['Close'].shift(1)
    data['BOS'] = data['Close'] > data['Prev_Close']
    data['FVG'] = (data['High'] - data['Low'].shift(1)) > 0.5  # Threshold example

    signals = data[(data['BOS']) | (data['FVG'])]
    signals['Symbol'] = symbol
    all_signals = pd.concat([all_signals, signals], ignore_index=True)

# -------------------------
# Step 3: Log Trades / Setups
# -------------------------
def log_trade(symbol, time, price, signal_type, result=""):
    with open(journal_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), symbol, time, price, signal_type, result])

for index, row in all_signals.iterrows():
    signal_type = "BOS" if row['BOS'] else "FVG"
    log_trade(row['Symbol'], row['Datetime'], row['Close'], signal_type)

# -------------------------
# Step 4: Optional AI Analysis
# -------------------------
if client:
    for index, row in all_signals.iterrows():
        prompt = f"Analyze this trade setup for {row['Symbol']}:\nTime: {row['Datetime']}\nPrice: {row['Close']}\nSignal: {'BOS' if row['BOS'] else 'FVG'}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )
        print(f"AI Advice for {row['Symbol']} at {row['Datetime']}: {response.choices[0].message.content}")

# -------------------------
# Step 5: Optional Telegram Alerts
# -------------------------
if bot:
    for index, row in all_signals.iterrows():
        signal_type = "BOS" if row['BOS'] else "FVG"
        message = f"{row['Symbol']} signal detected!\nTime: {row['Datetime']}\nPrice: {row['Close']}\nSignal: {signal_type}"
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# -------------------------
# Step 6: Basic P&L & Win Rate Calculation
# -------------------------
journal = pd.read_csv(journal_file)
if not journal.empty:
    total_trades = len(journal)
    # Example: random P&L simulation, replace with actual trade results later
    journal['Result'] = journal['Result'].replace("", 1)  # Dummy win = 1
    wins = journal[journal['Result'] > 0].shape[0]
    win_rate = (wins / total_trades) * 100
    print(f"Total Trades: {total_trades}, Win Rate: {win_rate:.2f}%")

# -------------------------
# Step 7: Plot Signals
# -------------------------
plt.figure(figsize=(12,6))
for symbol in symbols:
    data = yf.download(symbol, period=lookback_days, interval=interval)
    data.reset_index(inplace=True)
    plt.plot(data['Close'], label=f'{symbol} Close')
    sigs = all_signals[all_signals['Symbol']==symbol]
    plt.scatter(sigs.index, sigs['Close'], label=f'{symbol} Signals', s=50)

plt.title("Trading Signals")
plt.xlabel("Time Index")
plt.ylabel("Price")
plt.legend()
plt.show()
