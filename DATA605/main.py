"""
Real-Time Bitcoin Price Analysis Using Prefect.

This script defines a real-time ETL flow that fetches Bitcoin price data from
the CoinGecko API, validates, saves, analyzes, visualizes, and issues basic alerts
on price spikes.

Future scope includes 5-minute interval scheduling and enhanced alert mechanisms.
"""

# ======================================================
# Standard Library Imports
# ======================================================

import os
import sys
import logging

# ======================================================
# Third-party Imports
# ======================================================

import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from prefect import flow, task, get_run_logger

# ======================================================
# Configuration
# ======================================================

# Load environment variables from .env file.
load_dotenv()

# Configure stdout encoding for UTF-8.
sys.stdout.reconfigure(encoding='utf-8')

# Initialize logging.
logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)

# ======================================================
# Define Tasks
# ======================================================

@task
def fetch_bitcoin_price() -> dict:
    """
    Fetch Bitcoin price data from the CoinGecko API.

    :return: Dictionary containing price and timestamp.
    """
    logger = get_run_logger()
    url = os.getenv("API_URL")
    response = requests.get(url)
    data = response.json()
    logger.info(f"Bitcoin Price Fetched: ${data['bitcoin']['usd']}")
    return {"price": data["bitcoin"]["usd"], "timestamp": response.headers.get("Date")}

@task
def validate_data(data: dict) -> dict:
    """
    Validate that the fetched price exists and is positive.

    :param data: Dictionary containing price and timestamp.
    :return: Validated data dictionary.
    """
    assert "price" in data and data["price"] > 0
    return data

@task
def load_to_csv(data: dict) -> None:
    """
    Append fetched data to bitcoin_data.csv.

    :param data: Dictionary containing price and timestamp.
    """
    df = pd.DataFrame([data])
    file_exists = os.path.isfile("bitcoin_data.csv")
    df.to_csv("bitcoin_data.csv", mode='a', header=not file_exists, index=False)

@task
def analyze_data() -> pd.DataFrame:
    """
    Analyze Bitcoin price data and compute rolling averages.

    :return: DataFrame with price, timestamp, and rolling average.
    """
    df = pd.read_csv("bitcoin_data.csv", names=["price", "timestamp"], header=0)
    df["price"] = pd.to_numeric(df["price"], errors='coerce')
    df["rolling_avg"] = df["price"].rolling(window=2).mean()
    print(df.tail())
    return df

@task
def visualize_data(df: pd.DataFrame) -> None:
    """
    Generate and save a plot of Bitcoin price and rolling averages.

    :param df: DataFrame containing analyzed data.
    """
    if df.empty or "rolling_avg" not in df.columns:
        print("No data or missing rolling_avg.")
        return
    df.plot(x="timestamp", y=["price", "rolling_avg"], marker='o')
    plt.title("Bitcoin Price Trend")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("bitcoin_trend.png")
    print("Plot saved.")

@task
def alert_on_spike(df: pd.DataFrame) -> None:
    """
    Issue an alert if a significant price spike is detected.

    :param df: DataFrame containing analyzed data.
    """
    if df["price"].pct_change().iloc[-1] > 0.05:
        print("ALERT: Significant price spike detected!")

# ======================================================
# Define Flow
# ======================================================

@flow
def bitcoin_etl_flow() -> None:
    """
    Real-Time Bitcoin ETL flow using Prefect.
    """
    data = fetch_bitcoin_price()
    data = validate_data(data)
    load_to_csv(data)
    df = analyze_data()
    visualize_data(df)
    alert_on_spike(df)

# ======================================================
# Entry Point
# ======================================================

if __name__ == "__main__":
    bitcoin_etl_flow()