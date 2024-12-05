import pandas as pd 
import os
import time
from binance.client import Client
from binance.enums import *
import math
from dotenv import load_dotenv
load_dotenv()

print("\n===============================================SOLUSDT===============================================")
# Retrieve API keys from environment variables
api_key = os.getenv("KEY_BINANCE")
api_secret = os.getenv("SECRET_BINANCE")

# Initialize Binance client
client = Client(api_key, api_secret)

# Get symbol information for SOLUSDT
symbol_info = client.get_symbol_info("SOLUSDT")
lot_size_filter = next(f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE")
min_qty = float(lot_size_filter["minQty"])
max_qty = float(lot_size_filter["maxQty"])
step_size = float(lot_size_filter["stepSize"])


# Retrieve the minimum notional value
min_notional_filter = next((f for f in symbol_info["filters"] if f["filterType"] == "MIN_NOTIONAL"), None)
if min_notional_filter:
    min_notional = float(min_notional_filter["minNotional"])
else:
    # print("MIN_NOTIONAL filter not found for XRPUSDT. Setting a default value.")
    min_notional = 5.0  # Set a reasonable default value based on typical minimums

# Print lot size filter details
print("quantidade mínima: ", min_qty, "\nquantidade máxima: ", max_qty, "\npasso (de quanto em quanto se pode negociar): ", step_size)

# Define trading parameters
codigo_operado = "SOLUSDT"
ativo_operado = "SOL"
periodo = Client.KLINE_INTERVAL_30MINUTE

# Ensure the USDT amount is at least the minimum notional value
usdt_amount = 5.0

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
    print(f"Última média rápida: {ultima_media_rapida:.4f} | Última média lenta: {ultima_media_lenta:.4f}")
    
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
    step_size = float(lot_size_filter["stepSize"])
    precision = int(round(-math.log(step_size, 10)))
    
    # Adjust the quantity to the allowed precision
    quantidade = round(quantidade, precision)
    
     # Ensure the order value is above the minimum notional value
    order_value = quantidade * current_price
    if order_value < min_notional:
        # print(f"Order value {order_value:.2f} is below the minimum notional value {min_notional:.2f}. Adjusting quantity.")
        quantidade = math.ceil(min_notional / current_price * (10 ** precision)) / (10 ** precision)
    
    # Ensure the quantity is a valid string representation of a decimal number
    quantidade = f"{quantidade:.{precision}f}"
    
    # Trading logic based on moving averages
    if ultima_media_rapida > ultima_media_lenta:
        if posicao_atual == False:
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
            # Place a market sell order
            order = client.create_order(
                symbol=codigo_ativo,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=int(saldo_disponivel * 1000)/1000
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
    dados_atualizados = get_data(codigo=codigo_operado, intervalo=periodo)
    posicao_atual = estrategia_trading(dados_atualizados, codigo_operado, ativo_operado, usdt_amount, posicao_atual)
    if posicao_atual == True:
        conta = client.get_account()
        for ativo in conta["balances"]:
            if ativo["asset"] == ativo_operado:
                print("Posição atual em ", ativo_operado, ": ", ativo["free"], ativo_operado, f", isso equivale a {get_valores(ativo_operado, ativo['free']):.2f} USDT\n")
    else:
        conta = client.get_account()
        for ativo in conta["balances"]:
            if ativo["asset"] == "USDT":
                print("Posição atual: ", ativo["free"], "USDT\n")
    time.sleep(60*15)  # Wait for 15 minutes before the next iteration
