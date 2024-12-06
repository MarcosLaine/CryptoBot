import pandas as pd 
import os
import time
from binance.client import Client
from binance.enums import *
import math
from dotenv import load_dotenv
load_dotenv()

def create_info_box(symbol, min_qty, max_qty, step_size, current_price):
    print(f"\n╔═════════════════════════════════ {symbol} ════════════════════════════════╗")
    print(f"║ Quantidade mínima: {min_qty:<54}║")
    print(f"║ Quantidade máxima: {max_qty:<54}║")
    print(f"║ Passo: {step_size:<66}║")
    print(f"║ Preço atual: {current_price:<60}║")
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

# Get symbol information for SOLUSDT
symbol_info = client.get_symbol_info("SOLUSDT")

# Get current price for SOLUSDT
ticker = client.get_symbol_ticker(symbol="SOLUSDT")
current_price = float(ticker["price"])

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
codigo_operado = "SOLUSDT"
ativo_operado = "SOL"
periodo = Client.KLINE_INTERVAL_30MINUTE
usdt_amount = 5.5

def get_data(codigo, intervalo):
    candle = client.get_klines(symbol=codigo, interval=periodo, limit=1000)
    precos = pd.DataFrame(candle)
    precos.columns = ["tempo_abertura", "preco_abertura", "preco_maximo", "preco_minimo", "preco_fechamento", "volume", "tempo_fechamento", "moedas_negociadas", "numero_trades", "volume_ativo_base_compra", "volume_cotacao", "-"]
    precos = precos[["preco_fechamento", "tempo_fechamento"]]
    precos["tempo_fechamento"] = pd.to_datetime(precos["tempo_fechamento"], unit="ms").dt.tz_localize("UTC").dt.tz_convert("America/Sao_Paulo")
    return precos

def estrategia_trading(dados, codigo_ativo, ativo_operado, usdt_amount, posicao_atual):
    dados["media_rapida"] = dados["preco_fechamento"].rolling(window=7).mean()
    dados["media_lenta"] = dados["preco_fechamento"].rolling(window=40).mean()
    
    ultima_media_rapida = dados["media_rapida"].iloc[-1]
    ultima_media_lenta = dados["media_lenta"].iloc[-1]
    
    print_moving_averages(ultima_media_rapida, ultima_media_lenta)
    
    conta = client.get_account()
    
    for ativo in conta["balances"]:
        if ativo["asset"] == ativo_operado:
            saldo_disponivel = float(ativo["free"])
    
    ticker = client.get_symbol_ticker(symbol=codigo_ativo)
    current_price = float(ticker["price"])
    
    quantidade = usdt_amount / current_price
    precision = int(round(-math.log(step_size, 10)))
    quantidade = round(quantidade, precision)
    
    order_value = quantidade * current_price
    if order_value < min_notional:
        quantidade = math.ceil(min_notional / current_price * (10 ** precision)) / (10 ** precision)
    
    quantidade = f"{quantidade:.{precision}f}"
    
    if ultima_media_rapida > ultima_media_lenta:
        if not posicao_atual:
            order_value = float(quantidade) * current_price
            if order_value < min_notional:
                print_error_message(f"Cannot buy: Order value ({order_value:.2f} USDT) is below minimum notional ({min_notional} USDT)")
                return posicao_atual
            
            order = client.create_order(
                symbol=codigo_ativo,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantidade
            )
            print("║ Compra realizada                                                         ║")
            posicao_atual = True
            
    elif ultima_media_rapida < ultima_media_lenta:
        if posicao_atual:
            quantidade = float(saldo_disponivel)
            quantidade = math.floor(quantidade / step_size) * step_size
            order_value = quantidade * current_price
            
            if order_value < min_notional:
                print_error_message(f"Cannot sell: Order value ({order_value:.2f} USDT) is below minimum notional ({min_notional} USDT)")
                return posicao_atual
                
            try:
                order = client.create_order(
                    symbol=codigo_ativo,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_MARKET,
                    quantity=f"{quantidade:.{precision}f}"
                )
                print("║ Venda realizada                                                           ║")
                posicao_atual = False
            except Exception as e:
                print_error_message(f"Order failed: {e}")
            
    return posicao_atual

def get_valores(ativo_operado, saldo_disponivel):
    ticker = client.get_symbol_ticker(symbol=f"{ativo_operado}USDT")
    preco_ativo_em_usdt = float(ticker["price"])
    saldo_disponivel = float(saldo_disponivel)
    valor_ativo_em_usdt = saldo_disponivel * preco_ativo_em_usdt
    return valor_ativo_em_usdt

posicao_atual = True

while True:
    
    # Print initial info box
    create_info_box("SOLUSDT", min_qty, max_qty, step_size, current_price)
    dados_atualizados = get_data(codigo=codigo_operado, intervalo=periodo)
    posicao_atual = estrategia_trading(dados_atualizados, codigo_operado, ativo_operado, usdt_amount, posicao_atual)
    
    conta = client.get_account()
    
    if posicao_atual:
        for ativo in conta["balances"]:
            if ativo["asset"] == ativo_operado:
                valor_usdt = get_valores(ativo_operado, ativo["free"])
                print_position(ativo_operado, ativo["free"], valor_usdt)
    else:
        for ativo in conta["balances"]:
            if ativo["asset"] == "USDT":
                print_position(ativo_operado, ativo["free"], 0, is_positioned=False)
    time.sleep(60*15)
