from flask import Flask
import threading
from bot import main  # Usa sua lógica de trading já implementada

app = Flask(__name__)

@app.route('/')
def home():
    return "CryptoBot is running!"

@app.route('/start')
def start_bot():
    t = threading.Thread(target=main)
    t.start()
    return "CryptoBot started!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
