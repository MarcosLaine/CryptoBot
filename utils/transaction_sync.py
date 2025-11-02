import sqlite3
from binance.client import Client
import os
from dotenv import load_dotenv

DB_PATH = 'cryptobot.db'

def sync_transactions_from_binance(user_id):
    """
    Syncs transactions from Binance order history to the database.
    Only syncs orders that are not already in the database.
    """
    load_dotenv()
    api_key = os.getenv("KEY_BINANCE")
    api_secret = os.getenv("SECRET_BINANCE")
    client = Client(api_key, api_secret)
    
    ativos = ["BNBUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for ativo in ativos:
        try:
            # Get recent trades from Binance
            trades = client.get_my_trades(symbol=ativo, limit=500)
            
            for trade in trades:
                # Check if transaction already exists
                cursor.execute('''
                    SELECT id FROM transactions 
                    WHERE user_id = ? AND asset = ? 
                    AND quantity = ? AND price = ? AND timestamp = ?
                ''', (
                    user_id,
                    ativo,
                    float(trade['qty']),
                    float(trade['price']),
                    trade['time']
                ))
                
                if cursor.fetchone() is None:
                    # Insert new transaction
                    trade_type = 'BUY' if trade['isBuyer'] else 'SELL'
                    cursor.execute('''
                        INSERT INTO transactions 
                        (user_id, asset, type, quantity, price, total, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        ativo,
                        trade_type,
                        float(trade['qty']),
                        float(trade['price']),
                        float(trade['qty']) * float(trade['price']),
                        trade['time']
                    ))
            
            conn.commit()
        except Exception as e:
            print(f"Error syncing transactions for {ativo}: {e}")
            continue
    
    conn.close()
    print(f"Transactions synced for user {user_id}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        sync_transactions_from_binance(user_id)
    else:
        print("Usage: python transaction_sync.py <user_id>")

