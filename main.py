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
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("KEY_BINANCE")
    api_secret = os.getenv("SECRET_BINANCE")
    client = Client(api_key, api_secret)

    # List of assets to monitor
    ativos = ["BNBUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    intervalo = Client.KLINE_INTERVAL_30MINUTE

    while True: 
        os.system('cls')  # Clear terminal for readability
        posicoes = {}
        for ativo in ativos:
            ticker = client.get_symbol_ticker(symbol=ativo)
            preco_atual = float(ticker["price"])
            is_totally_positioned, not_positioned = verificar_estado_inicial(client, ativo, preco_atual)
            

            # Determine and print initial position status
            if is_totally_positioned:
                position_status = "totalmente posicionado (~ 20 USDT)"
            else:
                position_status = "não posicionado (~ 0 USDT)"
            posicoes[ativo] = (is_totally_positioned, not_positioned)
            print(f"Estado inicial para {ativo}: {position_status}")
        

        time.sleep(5)  # Small pause for clarity in terminal output

        for ativo in ativos:
            # Fetch asset information
            try:
                symbol_info = client.get_symbol_info(ativo)
                ticker = client.get_symbol_ticker(symbol=ativo)
                current_price = float(ticker["price"])
            except Exception as e:
                print(f"Error fetching data for {ativo}: {e}")
                continue

            # Extract lot size filter details
            lot_size_filter = next(f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE")
            min_qty = float(lot_size_filter["minQty"])
            max_qty = float(lot_size_filter["maxQty"])
            step_size = float(lot_size_filter["stepSize"])

            # Display asset information
            create_info_box(ativo, min_qty, max_qty, step_size, current_price)

            # Obtain historical data and calculate indicators
            dados = obter_dados_historicos(client, ativo, intervalo)
            dados = calcular_medias_moveis(dados)

            # Calculate and print moving averages
            media_rapida = dados["media_curta"].iloc[-1]
            media_lenta = dados["media_longa"].iloc[-1]
            print_moving_averages(media_rapida, media_lenta)

            # Sempre exibir a linha divisória
            print("╟──────────────────────────────────────────────────────────────────────────╢")

            # Execute trading strategy
            try:
                is_totally_positioned, status_message = estrategia_trading(
                    dados, ativo, client, is_totally_positioned, not_positioned
                )

                # Update the position state
                posicoes[ativo] = (is_totally_positioned, not_positioned)



                # Print status message if a trade was executed
                if status_message:
                    print(status_message)

            except Exception as e:
                print(f" Erro na execução da estratégia: {str(e)}")
                continue

            # Display detailed position
            try:
                conta = client.get_account()
                saldo_disponivel = conta["balances"]

                for saldo in saldo_disponivel:
                    if saldo["asset"] == ativo.split("USDT")[0]:
                        valor_usdt = float(saldo["free"]) * current_price
                        print(f" Valor em USDT: {valor_usdt:.2f}")
                        print(f" Posição em {ativo.split('USDT')[0]}: {saldo['free']} {ativo.split('USDT')[0]}")
                        break

            except Exception as e:
                print(f" Erro ao obter saldo: {str(e)}")
                continue

            # Separator for readability
            print("╚══════════════════════════════════════════════════════════════════════════╝")
            print()
            time.sleep(10)

        # Wait for 15 minutes before the next iteration
        time.sleep(60 * 15)

if __name__ == "__main__":
    os.system('cls')
    main()
