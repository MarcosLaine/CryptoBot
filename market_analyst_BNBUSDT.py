import pandas as pd 
import os
import time
from binance.client import Client
from binance.enums import *
import math
from dotenv import load_dotenv
import textwrap
load_dotenv()

def create_info_box(symbol, min_qty, max_qty, step_size):
    print(f"\n╔═════════════════════════════════ {symbol} ════════════════════════════════╗")
    print(f"║ Quantidade mínima: {min_qty:<54}║")
    print(f"║ Quantidade máxima: {max_qty:<54}║")
    print(f"║ Passo: {step_size:<66}║")
    print("╟──────────────────────────────────────────────────────────────────────────╢")

def print_moving_averages(rapida, lenta):
    print(f"║ Última média rápida: {rapida:.3f} | Última média lenta: {lenta:.3f}               ║")

def print_error_message(message):
    print(f"║ {message:<70}║")

def print_position(ativo, quantidade, valor_usdt, is_positioned=True):
    if is_positioned:
        message = f"Posição atual em {ativo}: {quantidade} {ativo} (={valor_usdt:.2f} USDT)"
    else:
        message = f"Posição atual: {quantidade} USDT"
    print(f"║ {message:<73}║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")


# Retrieve API keys from environment variables
api_key = os.getenv("KEY_BINANCE")
api_secret = os.getenv("SECRET_BINANCE")

# Initialize Binance client
client = Client(api_key, api_secret)

# Get symbol information for BNBUSDT
symbol_info = client.get_symbol_info("BNBUSDT")
lot_size_filter = next(f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE")
min_qty = float(lot_size_filter["minQty"])
max_qty = float(lot_size_filter["maxQty"])
step_size = float(lot_size_filter["stepSize"])

# Retrieve the minimum notional value
min_notional_filter = next((f for f in symbol_info["filters"] if f["filterType"] == "MIN_NOTIONAL"), None)
if min_notional_filter:
    min_notional = float(min_notional_filter["minNotional"])
else:
    min_notional = 5.5

# Define trading parameters
codigo_operado = "BNBUSDT"
ativo_operado = "BNB"
periodo = Client.KLINE_INTERVAL_30MINUTE
usdt_amount = 5.5

def get_data(codigo, intervalo):
    # Fetch historical kline data
    candle = client.get_klines(symbol=codigo, interval=periodo, limit=1000)
    precos = pd.DataFrame(candle)
    # Rename columns for clarity
    precos.columns = ["tempo_abertura", "preco_abertura", "preco_maximo", "preco_minimo", "preco_fechamento", "volume", "tempo_fechamento", "moedas_negociadas", "numero_trades", "volume_ativo_base_compra", "volume_cotacao", "-"]
    # Select relevant columns
    precos = precos[["preco_fechamento", "tempo_fechamento"]]
    # Convert timestamp to local timezone
    precos["tempo_fechamento"] = pd.to_datetime(precos["tempo_fechamento"], unit="ms").dt.tz_localize("UTC").dt.tz_convert("America/Sao_Paulo")
    
    return precos

def estrategia_trading(dados, codigo_ativo, ativo_operado, usdt_amount, posicao_atual):
    # Calculate moving averages
    dados["media_rapida"] = dados["preco_fechamento"].rolling(window=7).mean()
    dados["media_lenta"] = dados["preco_fechamento"].rolling(window=40).mean()
    
    # Get the latest moving averages
    ultima_media_rapida = dados["media_rapida"].iloc[-1]
    ultima_media_lenta = dados["media_lenta"].iloc[-1]
    
    # Print the latest moving averages
    print_moving_averages(ultima_media_rapida, ultima_media_lenta)
    
    # Get account information
    conta = client.get_account()
    
    # Retrieve available balance for the traded asset
    for ativo in conta["balances"]:
        if ativo["asset"] == ativo_operado:
            saldo_disponivel = float(ativo["free"])
    
    # Get current price of the asset
    ticker = client.get_symbol_ticker(symbol=codigo_ativo)
    current_price = float(ticker["price"])
    
    # Calculate the quantity to buy based on the USDT amount
    quantidade = usdt_amount / current_price
    
    # Determine the precision from step_size
    precision = int(round(-math.log(step_size, 10)))
    
    # Adjust the quantity to the allowed precision
    quantidade = round(quantidade, precision)
    
    # Ensure the order value is above the minimum notional value
    order_value = quantidade * current_price
    if order_value < min_notional:
        quantidade = math.ceil(min_notional / current_price * (10 ** precision)) / (10 ** precision)
    
    # Ensure the quantity is a valid string representation of a decimal number
    quantidade = f"{quantidade:.{precision}f}"
    
    # Trading logic based on moving averages
    if ultima_media_rapida > ultima_media_lenta:
        if posicao_atual == False:
            # Check if the buy order meets the minimum notional requirement
            order_value = float(quantidade) * current_price
            if order_value < min_notional:
                print_error_message(f"Cannot buy: Order value ({order_value:.2f} USDT) is below minimum notional ({min_notional} USDT)")
                return posicao_atual
            
            # Place a market buy order
            order = client.create_order(
                symbol=codigo_ativo,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantidade
            )
            print("Compra realizada")
            posicao_atual = True
            
    elif ultima_media_rapida < ultima_media_lenta:
        if posicao_atual == True:
            # Calculate the order value before placing the sell order
            quantidade = float(saldo_disponivel)
            quantidade = round(quantidade, precision)
            order_value = quantidade * current_price
            
            if order_value < min_notional:
                print_error_message(f"Cannot sell: Order value ({order_value:.2f} USDT) is below minimum notional ({min_notional} USDT)")
                return posicao_atual
                
            # Place a market sell order
            order = client.create_order(
                symbol=codigo_ativo,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=f"{quantidade:.{precision}f}"
            )
            print("Venda realizada")
            posicao_atual = False
            
    return posicao_atual

def get_valores(ativo_operado, saldo_disponivel):
    ticker = client.get_symbol_ticker(symbol=f"{ativo_operado}USDT")
    preco_ativo_em_usdt = float(ticker["price"])
    # Ensure saldo_disponivel is a float
    saldo_disponivel = float(saldo_disponivel)
    valor_ativo_em_usdt = saldo_disponivel * preco_ativo_em_usdt
    return valor_ativo_em_usdt

# Initialize current position status
posicao_atual = True

# Main loop to continuously fetch data and execute trading strategy
while True:
    create_info_box("BNBUSDT", min_qty, max_qty, step_size)
    dados_atualizados = get_data(codigo=codigo_operado, intervalo=periodo)
    posicao_atual = estrategia_trading(dados_atualizados, codigo_operado, ativo_operado, usdt_amount, posicao_atual)
    if posicao_atual == True:
        conta = client.get_account()
        for ativo in conta["balances"]:
            if ativo["asset"] == ativo_operado:
                print_position(ativo_operado, ativo["free"], get_valores(ativo_operado, ativo['free']))
    else:
        conta = client.get_account()
        for ativo in conta["balances"]:
            if ativo["asset"] == "USDT":
                print_position("USDT", ativo["free"], 0, False)
    time.sleep(60*15)  # Wait for 15 minutes before the next iteration
