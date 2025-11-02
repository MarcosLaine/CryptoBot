from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import sqlite3
import os
import time
from datetime import datetime, timedelta
import pandas as pd
from bot import main, run_bot_loop
import os as os_module
from binance.client import Client
from dotenv import load_dotenv
from utils.data import obter_dados_historicos
from Indicators.moving_averages import calcular_medias_moveis
from cryptography.fernet import Fernet
import base64

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Configurar CORS para permitir todas as origens e métodos
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=False,
     send_wildcard=True)

jwt = JWTManager(app)

# Database setup
DB_PATH = 'cryptobot.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset TEXT NOT NULL,
            type TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Portfolio snapshots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset TEXT NOT NULL,
            quantity REAL NOT NULL,
            value_usdt REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # API Keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            api_key TEXT NOT NULL,
            api_secret TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Bot status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            is_running INTEGER DEFAULT 0,
            started_at TIMESTAMP,
            stopped_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Bot settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            check_interval_minutes INTEGER DEFAULT 30,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Asset settings table - configuração de ativos e valores por usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset_symbol TEXT NOT NULL,
            asset_name TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            investment_amount REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, asset_symbol)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Threads management
bot_threads = {}
bot_stop_flags = {}

# Encryption key for API secrets (in production, use environment variable)
# Try to load from .env first, then from .encryption_key file, then generate new
ENCRYPTION_KEY_FILE = '.encryption_key'
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

if not ENCRYPTION_KEY:
    # Try to load from file if it exists
    if os.path.exists(ENCRYPTION_KEY_FILE):
        try:
            with open(ENCRYPTION_KEY_FILE, 'r') as f:
                ENCRYPTION_KEY = f.read().strip()
            print(f"Loaded ENCRYPTION_KEY from {ENCRYPTION_KEY_FILE}")
        except Exception as e:
            print(f"Error reading encryption key file: {e}. Generating new key.")
            ENCRYPTION_KEY = None

if not ENCRYPTION_KEY:
    # Generate new key and save it
    generated_key = Fernet.generate_key()
    ENCRYPTION_KEY = generated_key.decode()
    try:
        with open(ENCRYPTION_KEY_FILE, 'w') as f:
            f.write(ENCRYPTION_KEY)
        print(f"Generated new ENCRYPTION_KEY and saved to {ENCRYPTION_KEY_FILE}")
        print(f"WARNING: If you have existing encrypted API keys, you need to reconfigure them.")
    except Exception as e:
        print(f"Warning: Could not save encryption key to file: {e}")
        print(f"Warning: ENCRYPTION_KEY={ENCRYPTION_KEY}")
        print(f"Set this in your .env file or save it to {ENCRYPTION_KEY_FILE} for persistence.")
elif isinstance(ENCRYPTION_KEY, bytes):
    ENCRYPTION_KEY = ENCRYPTION_KEY.decode()

try:
    cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
except Exception as e:
    # If key is invalid, generate a new one
    print(f"Error with encryption key: {e}. Generating new key.")
    generated_key = Fernet.generate_key()
    ENCRYPTION_KEY = generated_key.decode()
    try:
        with open(ENCRYPTION_KEY_FILE, 'w') as f:
            f.write(ENCRYPTION_KEY)
    except:
        pass
    cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_secret(secret):
    return cipher_suite.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted_secret):
    """
    Descriptografa a API secret.
    Se a descriptografia falhar (por exemplo, chave diferente), retorna None.
    """
    try:
        return cipher_suite.decrypt(encrypted_secret.encode()).decode()
    except Exception as e:
        print(f"Error decrypting secret: {e}")
        print("This usually means the encryption key has changed. The user needs to reconfigure their API keys.")
        # Re-raise the exception so the caller knows decryption failed
        raise ValueError(f"Failed to decrypt API secret. This usually means the encryption key has changed. Please reconfigure your API keys.")

def get_binance_client(user_id=None):
    """
    Cria um cliente Binance com configurações apropriadas.
    O recvWindow é passado explicitamente nas chamadas de API que precisarem.
    """
    if user_id:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT api_key, api_secret FROM api_keys WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            api_key = result[0]
            try:
                api_secret = decrypt_secret(result[1])
            except ValueError as e:
                # If decryption fails, raise a more user-friendly error
                raise ValueError("API keys encryption error. Please reconfigure your API keys in the settings.")
        else:
            raise ValueError("API keys not configured for this user")
    else:
        # Fallback to .env (backward compatibility)
        load_dotenv()
        api_key = os_module.getenv("KEY_BINANCE")
        api_secret = os_module.getenv("SECRET_BINANCE")
    
    # Criar cliente Binance
    client = Client(api_key, api_secret)
    
    return client

def sync_binance_time(client):
    """
    Sincroniza o tempo com o servidor Binance e ajusta o recvWindow.
    Retorna o offset em milissegundos (diferença entre tempo local e servidor).
    """
    try:
        server_time = client.get_server_time()
        server_timestamp = server_time['serverTime']
        local_timestamp = int(time.time() * 1000)
        offset = server_timestamp - local_timestamp
        
        # Se a diferença for maior que 5 segundos, pode causar problemas
        if abs(offset) > 5000:
            print(f"Warning: Time offset detected: {offset}ms. Consider syncing your system clock.")
        
        return offset
    except Exception as e:
        print(f"Error syncing with Binance time: {e}")
        return 0

@app.route('/')
def home():
    return jsonify({"message": "CryptoBot API is running!"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        password_hash = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        access_token = create_access_token(identity=str(user_id))
        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "user_id": user_id
        }), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Username already exists"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[1], password):
        access_token = create_access_token(identity=str(user[0]))
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user_id": user[0]
        }), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio():
    user_id = int(get_jwt_identity())
    try:
        client = get_binance_client(user_id)
    except ValueError as e:
        return jsonify({"error": "API keys not configured. Please configure your API keys first."}), 400
    except Exception as e:
        return jsonify({"error": f"Error creating Binance client: {str(e)}"}), 500
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user's enabled assets
        cursor.execute('''
            SELECT asset_symbol, asset_name, investment_amount 
            FROM asset_settings 
            WHERE user_id = ? AND enabled = 1
        ''', (user_id,))
        user_assets = cursor.fetchall()
        
        # If no custom settings, use default assets
        if not user_assets:
            ativos = [a["symbol"] for a in TOP_ASSETS[:5]]  # Default: first 5
        else:
            ativos = [row[0] for row in user_assets]
        
        portfolio_data = []
        total_value = 0
        total_invested = 0
        
        # Get account once, outside the loop
        try:
            account = client.get_account(recvWindow=60000)
            if not account or "balances" not in account:
                conn.close()
                return jsonify({"error": "Invalid response from Binance account API"}), 500
            balances = account.get("balances", [])
        except Exception as e:
            conn.close()
            return jsonify({"error": f"Error getting account from Binance: {str(e)}"}), 500
        
        for ativo in ativos:
            try:
                ticker = client.get_symbol_ticker(symbol=ativo)
                current_price = float(ticker["price"])
                asset_name = ativo.replace("USDT", "")
                
                # Get current balance from already fetched account
                quantity = 0
                for balance in balances:
                    if balance.get("asset") == asset_name:
                        quantity = float(balance.get("free", 0))
                        break
                
                value_usdt = quantity * current_price
                
                # Calculate invested amount from transactions
                cursor.execute('''
                    SELECT SUM(total) FROM transactions 
                    WHERE user_id = ? AND asset = ? AND type = 'BUY'
                ''', (user_id, ativo))
                invested_buy = cursor.fetchone()[0] or 0
                
                cursor.execute('''
                    SELECT SUM(total) FROM transactions 
                    WHERE user_id = ? AND asset = ? AND type = 'SELL'
                ''', (user_id, ativo))
                invested_sell = cursor.fetchone()[0] or 0
                
                invested = invested_buy - invested_sell
                total_invested += invested
                total_value += value_usdt
                
                # Get moving averages
                dados = obter_dados_historicos(client, ativo, Client.KLINE_INTERVAL_30MINUTE)
                dados = calcular_medias_moveis(dados)
                media_curta_val = dados["media_curta"].iloc[-1] if len(dados) > 0 else None
                media_longa_val = dados["media_longa"].iloc[-1] if len(dados) > 0 else None
                media_curta = float(media_curta_val) if media_curta_val is not None and not pd.isna(media_curta_val) else 0
                media_longa = float(media_longa_val) if media_longa_val is not None and not pd.isna(media_longa_val) else 0
                
                return_amount = value_usdt - invested if invested > 0 else 0
                return_percentage = ((value_usdt - invested) / invested * 100) if invested > 0 else 0
                
                portfolio_data.append({
                    "asset": asset_name,
                    "symbol": ativo,
                    "quantity": quantity,
                    "current_price": current_price,
                    "value_usdt": value_usdt,
                    "invested": invested,
                    "return_amount": return_amount,
                    "return_percentage": return_percentage,
                    "media_curta": media_curta,
                    "media_longa": media_longa
                })
            except Exception as e:
                print(f"Error processing {ativo}: {e}")
                continue
        
        conn.close()
        
        total_return = total_value - total_invested
        total_return_percentage = ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
        
        return jsonify({
            "portfolio": portfolio_data,
            "total_value": total_value,
            "total_invested": total_invested,
            "total_return": total_return,
            "total_return_percentage": total_return_percentage
        }), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_portfolio: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 50, type=int)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT asset, type, quantity, price, total, timestamp 
        FROM transactions 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))
    
    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            "asset": row[0],
            "type": row[1],
            "quantity": row[2],
            "price": row[3],
            "total": row[4],
            "timestamp": row[5]
        })
    
    conn.close()
    return jsonify({"transactions": transactions}), 200

@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = int(get_jwt_identity())
    try:
        client = get_binance_client(user_id)
    except ValueError:
        return jsonify({"error": "API keys not configured. Please configure your API keys first."}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get account balance
        try:
            account = client.get_account(recvWindow=60000)
            if not account or "balances" not in account:
                conn.close()
                return jsonify({"error": "Invalid response from Binance API"}), 500
        except Exception as e:
            conn.close()
            return jsonify({"error": f"Error accessing Binance account: {str(e)}"}), 500
        
        usdt_balance = 0
        balances = account.get("balances", [])
        for balance in balances:
            if balance.get("asset") == "USDT":
                usdt_balance = float(balance.get("free", 0))
                break
        
        # Get initial investment (first transaction total)
        cursor.execute('''
            SELECT SUM(total) FROM transactions 
            WHERE user_id = ? AND type = 'BUY'
        ''', (user_id,))
        total_invested = cursor.fetchone()[0] or 0
        
        # Get total transactions count
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ?', (user_id,))
        total_transactions = cursor.fetchone()[0]
        
        # Get user's enabled assets
        cursor.execute('''
            SELECT asset_symbol 
            FROM asset_settings 
            WHERE user_id = ? AND enabled = 1
        ''', (user_id,))
        user_assets_result = cursor.fetchall()
        
        # If no custom settings, use default assets
        if not user_assets_result:
            ativos = [a["symbol"] for a in TOP_ASSETS[:5]]  # Default: first 5
        else:
            ativos = [row[0] for row in user_assets_result]
        
        # Get active positions count
        active_positions = 0
        for ativo in ativos:
            asset_name = ativo.replace("USDT", "")
            for balance in balances:
                if balance.get("asset") == asset_name and float(balance.get("free", 0)) > 0:
                    active_positions += 1
                    break
        
        conn.close()
        
        return jsonify({
            "usdt_balance": usdt_balance,
            "total_invested": total_invested,
            "total_transactions": total_transactions,
            "active_positions": active_positions
        }), 200
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_stats: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/api-keys', methods=['GET'])
@jwt_required()
def get_api_keys():
    """Get API keys for current user (without secret)"""
    user_id = int(get_jwt_identity())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT api_key FROM api_keys WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        # Return masked API key
        api_key = result[0]
        masked_key = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else '****'
        return jsonify({"has_keys": True, "api_key_masked": masked_key}), 200
    else:
        return jsonify({"has_keys": False}), 200

@app.route('/api/api-keys', methods=['POST'])
@jwt_required()
def save_api_keys():
    """Save or update API keys for current user"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    api_key = data.get('api_key')
    api_secret = data.get('api_secret')
    
    if not api_key or not api_secret:
        return jsonify({"error": "API key and secret are required"}), 400
    
    # Validate API keys by trying to create a client
    try:
        # Criar cliente para teste
        test_client = Client(api_key, api_secret)
        
        # Sincronizar tempo antes do teste
        try:
            server_time = test_client.get_server_time()
            server_timestamp = server_time['serverTime']
            local_timestamp = int(time.time() * 1000)
            offset = server_timestamp - local_timestamp
            
            if abs(offset) > 5000:
                print(f"Warning: Time offset detected: {offset}ms")
        except:
            pass
        
        # Test connection - agora com recvWindow explícito se necessário
        test_client.get_account(recvWindow=60000)
        
    except Exception as e:
        error_msg = str(e)
        # Mensagem mais amigável para erro de timestamp
        if "recvWindow" in error_msg or "Timestamp" in error_msg or "-1021" in error_msg:
            return jsonify({
                "error": "Erro de sincronização de tempo. O problema persiste mesmo com recvWindow aumentado. Tente: 1) Verificar conexão de internet, 2) Reiniciar o servidor, 3) Aguardar alguns minutos e tentar novamente. Se o problema persistir, pode ser necessário ajustar manualmente o relógio do sistema."
            }), 400
        return jsonify({"error": f"Chaves de API inválidas: {error_msg}"}), 400
    
    # Encrypt and save
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        encrypted_secret = encrypt_secret(api_secret)
        cursor.execute('''
            INSERT OR REPLACE INTO api_keys (user_id, api_key, api_secret, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, api_key, encrypted_secret))
        conn.commit()
        conn.close()
        return jsonify({"message": "API keys saved successfully"}), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot/status', methods=['GET'])
@jwt_required()
def get_bot_status():
    """Get bot status for current user"""
    user_id = int(get_jwt_identity())
    
    # Check if thread actually exists and is alive
    thread_is_alive = user_id in bot_threads and bot_threads[user_id].is_alive()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_running, started_at, stopped_at FROM bot_status WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    # If database says running but thread is not alive, fix the database
    if result and bool(result[0]) and not thread_is_alive:
        cursor.execute('''
            UPDATE bot_status 
            SET is_running = 0, stopped_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        is_running = False
    elif result:
        is_running = bool(result[0])
        # Also verify thread is actually alive if database says running
        if is_running and not thread_is_alive:
            # Thread died but database wasn't updated - fix it
            cursor.execute('''
                UPDATE bot_status 
                SET is_running = 0, stopped_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            is_running = False
    else:
        is_running = False
    
    conn.close()
    
    return jsonify({
        "is_running": is_running and thread_is_alive,  # Both must be true
        "started_at": result[1] if result else None,
        "stopped_at": result[2] if result else None
    }), 200

@app.route('/api/bot/start', methods=['POST'])
@jwt_required()
def start_bot():
    """Start bot for current user"""
    user_id = int(get_jwt_identity())
    
    # Check if bot is already running
    if user_id in bot_threads and bot_threads[user_id].is_alive():
        return jsonify({"error": "Bot is already running"}), 400
    
    # Check if API keys are configured
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT api_key, api_secret FROM api_keys WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"error": "API keys not configured. Please configure your API keys first."}), 400
    
    try:
        api_key = result[0]
        try:
            api_secret = decrypt_secret(result[1])
        except ValueError as e:
            return jsonify({"error": "API keys encryption error. The encryption key has changed. Please reconfigure your API keys."}), 400
        
        # Create stop flag for this user
        stop_flag = {'stop': False}
        bot_stop_flags[user_id] = stop_flag
        
        # Get bot settings (check interval)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT check_interval_minutes FROM bot_settings WHERE user_id = ?', (user_id,))
        settings_result = cursor.fetchone()
        check_interval_minutes = settings_result[0] if settings_result else 30
        
        # Get enabled assets for this user
        cursor.execute('''
            SELECT asset_symbol 
            FROM asset_settings 
            WHERE user_id = ? AND enabled = 1
        ''', (user_id,))
        user_assets_result = cursor.fetchall()
        
        if user_assets_result:
            enabled_assets = [row[0] for row in user_assets_result]
        else:
            # Default: first 5 assets
            enabled_assets = [a["symbol"] for a in TOP_ASSETS[:5]]
        
        conn.close()
        
        # Start bot in a new thread
        thread = threading.Thread(
            target=run_bot_loop,
            args=(api_key, api_secret, stop_flag, user_id, check_interval_minutes, enabled_assets),
            daemon=True
        )
        thread.start()
        bot_threads[user_id] = thread
        
        # Update database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO bot_status (user_id, is_running, started_at, stopped_at)
            VALUES (?, 1, CURRENT_TIMESTAMP, NULL)
        ''', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Bot started successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
@jwt_required()
def stop_bot():
    """Stop bot for current user"""
    user_id = int(get_jwt_identity())
    
    # Check if thread actually exists and is alive
    thread_is_alive = user_id in bot_threads and bot_threads[user_id].is_alive()
    
    # If thread doesn't exist but database says running, just fix the database
    if not thread_is_alive:
        # Clean up any stale references
        if user_id in bot_threads:
            del bot_threads[user_id]
        if user_id in bot_stop_flags:
            del bot_stop_flags[user_id]
        
        # Fix database state
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bot_status 
            SET is_running = 0, stopped_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Bot was already stopped. Status synchronized."}), 200
    
    try:
        # Set stop flag if it exists
        if user_id in bot_stop_flags:
            bot_stop_flags[user_id]['stop'] = True
        
        # Wait for thread to finish (with timeout)
        if user_id in bot_threads:
            thread = bot_threads[user_id]
            if thread.is_alive():
                thread.join(timeout=5)  # Wait up to 5 seconds
            
            # Remove thread reference
            del bot_threads[user_id]
        
        # Remove stop flag
        if user_id in bot_stop_flags:
            del bot_stop_flags[user_id]
        
        # Update database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bot_status 
            SET is_running = 0, stopped_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Bot stopped successfully"}), 200
    except Exception as e:
        # Even if there's an error, try to fix the database state
        try:
            if user_id in bot_threads:
                del bot_threads[user_id]
            if user_id in bot_stop_flags:
                del bot_stop_flags[user_id]
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE bot_status 
                SET is_running = 0, stopped_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
        except:
            pass
        
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot/settings', methods=['GET'])
@jwt_required()
def get_bot_settings():
    """Get bot settings for current user"""
    user_id = int(get_jwt_identity())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT check_interval_minutes FROM bot_settings WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify({
            "check_interval_minutes": result[0]
        }), 200
    else:
        # Return default if not configured
        return jsonify({
            "check_interval_minutes": 30
        }), 200

@app.route('/api/bot/settings', methods=['POST'])
@jwt_required()
def save_bot_settings():
    """Save bot settings for current user"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    check_interval_minutes = data.get('check_interval_minutes')
    
    if not check_interval_minutes:
        return jsonify({"error": "check_interval_minutes is required"}), 400
    
    # Validate interval (between 1 and 1440 minutes - 1 day)
    try:
        check_interval_minutes = int(check_interval_minutes)
        if check_interval_minutes < 1 or check_interval_minutes > 1440:
            return jsonify({"error": "Interval must be between 1 and 1440 minutes (24 hours)"}), 400
    except ValueError:
        return jsonify({"error": "check_interval_minutes must be a number"}), 400
    
    # Check if bot is running
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_running FROM bot_status WHERE user_id = ?', (user_id,))
    status_result = cursor.fetchone()
    is_running = status_result and bool(status_result[0])
    
    if is_running:
        conn.close()
        return jsonify({
            "error": "Cannot change settings while bot is running. Please stop the bot first."
        }), 400
    
    # Save settings
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO bot_settings (user_id, check_interval_minutes, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, check_interval_minutes))
        conn.commit()
        conn.close()
        return jsonify({
            "message": "Settings saved successfully",
            "check_interval_minutes": check_interval_minutes
        }), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync-transactions', methods=['POST'])
@jwt_required()
def sync_transactions():
    """Sync transactions from Binance order history"""
    user_id = int(get_jwt_identity())
    try:
        client = get_binance_client(user_id)
    except ValueError:
        return jsonify({"error": "API keys not configured. Please configure your API keys first."}), 400
    
    try:
        ativos = ["BNBUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        synced_count = 0
        
        for ativo in ativos:
            try:
                trades = client.get_my_trades(symbol=ativo, limit=500, recvWindow=60000)
                
                for trade in trades:
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
                        synced_count += 1
            except Exception as e:
                print(f"Error syncing transactions for {ativo}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": f"Synced {synced_count} new transactions",
            "count": synced_count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lista das 10 moedas mais comuns da Binance
TOP_ASSETS = [
    {"symbol": "BTCUSDT", "name": "Bitcoin (BTC)"},
    {"symbol": "ETHUSDT", "name": "Ethereum (ETH)"},
    {"symbol": "BNBUSDT", "name": "Binance Coin (BNB)"},
    {"symbol": "SOLUSDT", "name": "Solana (SOL)"},
    {"symbol": "XRPUSDT", "name": "Ripple (XRP)"},
    {"symbol": "ADAUSDT", "name": "Cardano (ADA)"},
    {"symbol": "DOGEUSDT", "name": "Dogecoin (DOGE)"},
    {"symbol": "MATICUSDT", "name": "Polygon (MATIC)"},
    {"symbol": "DOTUSDT", "name": "Polkadot (DOT)"},
    {"symbol": "AVAXUSDT", "name": "Avalanche (AVAX)"}
]

@app.route('/api/assets', methods=['GET'])
@jwt_required()
def get_available_assets():
    """Get list of available assets"""
    return jsonify({"assets": TOP_ASSETS}), 200

@app.route('/api/assets/settings', methods=['GET'])
@jwt_required()
def get_asset_settings():
    """Get asset settings for current user"""
    user_id = int(get_jwt_identity())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get user's asset settings
    cursor.execute('''
        SELECT asset_symbol, asset_name, enabled, investment_amount 
        FROM asset_settings 
        WHERE user_id = ?
    ''', (user_id,))
    user_settings = {row[0]: {"enabled": bool(row[2]), "investment_amount": row[3]} for row in cursor.fetchall()}
    
    conn.close()
    
    # Merge with default assets, including user settings
    assets_with_settings = []
    for asset in TOP_ASSETS:
        symbol = asset["symbol"]
        if symbol in user_settings:
            assets_with_settings.append({
                **asset,
                "enabled": user_settings[symbol]["enabled"],
                "investment_amount": user_settings[symbol]["investment_amount"]
            })
        else:
            # Default: enabled, no investment amount set
            assets_with_settings.append({
                **asset,
                "enabled": True,
                "investment_amount": 0
            })
    
    return jsonify({"assets": assets_with_settings}), 200

@app.route('/api/reset-transactions', methods=['POST'])
@jwt_required()
def reset_transactions():
    """Reset all transactions for current user (resets total invested and return calculations)"""
    user_id = int(get_jwt_identity())
    
    # Check if bot is running
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_running FROM bot_status WHERE user_id = ?', (user_id,))
    status_result = cursor.fetchone()
    is_running = status_result and bool(status_result[0])
    
    if is_running:
        conn.close()
        return jsonify({
            "error": "Cannot reset transactions while bot is running. Please stop the bot first."
        }), 400
    
    try:
        # Delete all transactions for this user
        cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
        
        # Also delete portfolio snapshots
        cursor.execute('DELETE FROM portfolio_snapshots WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "message": "Transactions and portfolio data reset successfully. Total invested and return will be recalculated from new transactions."
        }), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/assets/settings', methods=['POST'])
@jwt_required()
def save_asset_settings():
    """Save asset settings for current user"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    assets = data.get('assets', [])
    
    if not isinstance(assets, list):
        return jsonify({"error": "assets must be a list"}), 400
    
    # Check if bot is running
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT is_running FROM bot_status WHERE user_id = ?', (user_id,))
    status_result = cursor.fetchone()
    is_running = status_result and bool(status_result[0])
    
    if is_running:
        conn.close()
        return jsonify({
            "error": "Cannot change asset settings while bot is running. Please stop the bot first."
        }), 400
    
    try:
        for asset in assets:
            symbol = asset.get('symbol')
            name = asset.get('name')
            enabled = asset.get('enabled', False)
            investment_amount = asset.get('investment_amount', 0)
            
            # Validate asset is in our list
            if symbol not in [a["symbol"] for a in TOP_ASSETS]:
                continue
            
            # Validate investment amount
            try:
                investment_amount = float(investment_amount)
                if investment_amount < 0:
                    return jsonify({"error": f"Investment amount for {symbol} must be positive"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid investment amount for {symbol}"}), 400
            
            # Save or update
            cursor.execute('''
                INSERT OR REPLACE INTO asset_settings 
                (user_id, asset_symbol, asset_name, enabled, investment_amount, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, symbol, name, 1 if enabled else 0, investment_amount))
        
        conn.commit()
        conn.close()
        return jsonify({"message": "Asset settings saved successfully"}), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/start')
def start_bot_legacy():
    """Legacy endpoint - starts bot with .env keys"""
    t = threading.Thread(target=main)
    t.start()
    return jsonify({"message": "CryptoBot started!"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
