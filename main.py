import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
import asyncio
import json

from clients import KalshiHttpClient, KalshiWebSocketClient, Environment

# Load environment variables
load_dotenv()
env = Environment.PROD # toggle environment here
KEYID = os.getenv('DEMO_KEYID') if env == Environment.DEMO else os.getenv('PROD_KEYID')
KEYFILE = os.getenv('DEMO_KEYFILE') if env == Environment.DEMO else os.getenv('PROD_KEYFILE')

try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None  # Provide the password if your key is encrypted
        )
except FileNotFoundError:
    raise FileNotFoundError(f"Private key file not found at {KEYFILE}")
except Exception as e:
    raise Exception(f"Error loading private key: {str(e)}")

# Initialize the HTTP client
client = KalshiHttpClient(
    key_id=KEYID,
    private_key=private_key,
    environment=env
)

# Get account balance
balance = client.get_balance()
print(f"Balance: {json.dumps(balance, indent=4)} \n")

# positions = client.get_positions()
# print(f"Positions: {json.dumps(positions, indent=4)} \n")

# incentive = client.get_market_incentive()
# print(f"Incentive: {json.dumps(incentive, indent=4)} \n")

# tickers = client.get_ticker('KXLOWTDEN-26JAN11-T26')
# print(f"Tickers: {json.dumps(tickers, indent=4)} \n")

# Initialize the WebSocket client
# ws_client = KalshiWebSocketClient(
#     key_id=KEYID,
#     private_key=private_key,
#     environment=env
# )

# # Connect via WebSocket
# asyncio.run(ws_client.connect())