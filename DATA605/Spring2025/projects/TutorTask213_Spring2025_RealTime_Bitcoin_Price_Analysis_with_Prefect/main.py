# main.py
# Prefect Bitcoin ETL flow script
from prefect import flow, task

import requests
import pandas as pd
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')


@task
def fetch_bitcoin_price():
    from prefect import get_run_logger
    logger = get_run_logger()

    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()

    logger.info(f"📈 Bitcoin Price Fetched: ${data['bitcoin']['usd']}")

    return {
        "price": data["bitcoin"]["usd"],
        "timestamp": response.headers.get("Date")
    }

from prefect import get_run_logger

@task
def validate_data(data):
    assert "price" in data and data["price"] > 0
    return data

@task
def load_to_csv(data):
    df = pd.DataFrame([data])
    file_exists = os.path.isfile("bitcoin_data.csv")
    df.to_csv("bitcoin_data.csv", mode='a', header=not file_exists, index=False)

@task
def analyze_data():
    import pandas as pd

    df = pd.read_csv("bitcoin_data.csv", names=["price", "timestamp"], header=0)
    df["price"] = pd.to_numeric(df["price"], errors='coerce')
    df["rolling_avg"] = df["price"].rolling(window=2).mean()
    print(df.tail())  # For debug
    return df

@task
def visualize_data(df):
    import matplotlib.pyplot as plt

    if df.empty or "rolling_avg" not in df.columns:
        print("⚠️ No data or missing rolling_avg.")
        return

    df.plot(x="timestamp", y=["price", "rolling_avg"], marker='o')
    plt.title("Bitcoin Price Trend")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("bitcoin_trend.png")
    print("✅ Plot saved!")

@task
def alert_on_spike(df):
    if df["price"].pct_change().iloc[-1] > 0.05:
        print("🚨 ALERT: Significant price spike detected!")

@flow
def bitcoin_etl_flow():
    data = fetch_bitcoin_price()
    data = validate_data(data)
    load_to_csv(data)
    df = analyze_data()
    visualize_data(df)
    alert_on_spike(df)

if __name__ == "__main__":
    bitcoin_etl_flow()
