import os
from binance.client import Client
from dotenv import load_dotenv
import time
load_dotenv()

api_key = os.getenv("KEY_BINANCE")
api_secret = os.getenv("SECRET_BINANCE")

client = Client(api_key, api_secret)

def create_info_box(usdt_balance):
    print(f"\n╔═══════════════════════════════════ USDT ═════════════════════════════════╗")
    print(f"║ USDT Balance on your account: {usdt_balance['free']:<43}║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")


while True:
    balance = client.get_account()

    # Find the USDT balance
    usdt_balance = next((item for item in balance['balances'] if item['asset'] == 'USDT'), None)

    # Print the USDT balance
    create_info_box(usdt_balance)
    time.sleep(60*15)
