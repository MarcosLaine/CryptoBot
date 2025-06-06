import os
import time
from binance.client import Client
from dotenv import load_dotenv
from utils.data import obter_dados_historicos
from Indicators.moving_averages import calcular_medias_moveis
from src.strategy.tranding_strategy import estrategia_trading
from src.information.show_info import create_info_box, print_moving_averages, print_position
from src.information.check_position import verificar_estado_inicial

def main():
    load_dotenv()
    api_key = os.getenv("KEY_BINANCE")
    api_secret = os.getenv("SECRET_BINANCE")
    client = Client(api_key, api_secret)

    ativos = ["BNBUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    intervalo = Client.KLINE_INTERVAL_30MINUTE
    posicoes = {}

    for ativo in ativos:
        try:
            ticker = client.get_symbol_ticker(symbol=ativo)
            preco_atual = float(ticker["price"])
            is_totally_positioned, not_positioned = verificar_estado_inicial(client, ativo, preco_atual)
            posicoes[ativo] = (is_totally_positioned, not_positioned)
        except Exception as e:
            print(f"Erro ao obter posição inicial de {ativo}: {e}")
            continue

    for ativo in ativos:
        try:
            symbol_info = client.get_symbol_info(ativo)
            ticker = client.get_symbol_ticker(symbol=ativo)
            current_price = float(ticker["price"])

            lot_size_filter = next(f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE")
            min_qty = float(lot_size_filter["minQty"])
            max_qty = float(lot_size_filter["maxQty"])
            step_size = float(lot_size_filter["stepSize"])

            create_info_box(ativo, min_qty, max_qty, step_size, current_price)

            dados = obter_dados_historicos(client, ativo, intervalo)
            dados = calcular_medias_moveis(dados)

            media_rapida = dados["media_curta"].iloc[-1]
            media_lenta = dados["media_longa"].iloc[-1]
            print_moving_averages(media_rapida, media_lenta)

            print("╟──────────────────────────────────────────────────────────────────────────╢")

            is_totally_positioned, not_positioned = posicoes[ativo]
            is_totally_positioned, status_message = estrategia_trading(
                dados, ativo, client, is_totally_positioned, not_positioned
            )
            posicoes[ativo] = (is_totally_positioned, not_positioned)

            if status_message:
                print(status_message)

            conta = client.get_account()
            for saldo in conta["balances"]:
                if saldo["asset"] == ativo.split("USDT")[0]:
                    valor_usdt = float(saldo["free"]) * current_price
                    print(f" Valor em USDT: {valor_usdt:.2f}")
                    print(f" Posição em {ativo.split('USDT')[0]}: {saldo['free']} {ativo.split('USDT')[0]}")
                    break

            print("╚══════════════════════════════════════════════════════════════════════════╝")
            print()

        except Exception as e:
            print(f"Erro ao processar {ativo}: {e}")
            continue

if __name__ == "__main__":
    main()
