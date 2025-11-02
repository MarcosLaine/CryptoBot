import os
import time
from binance.client import Client
from dotenv import load_dotenv
from utils.data import obter_dados_historicos
from Indicators.moving_averages import calcular_medias_moveis
from src.strategy.tranding_strategy import estrategia_trading
from src.information.show_info import create_info_box, print_moving_averages, print_position
from src.information.check_position import verificar_estado_inicial

def run_bot_loop(api_key=None, api_secret=None, stop_flag=None, user_id=None, check_interval_minutes=30, enabled_assets=None):
    """
    Roda o bot em loop contínuo até que stop_flag seja definido como True.
    
    Args:
        api_key: Chave API Binance
        api_secret: Secret API Binance
        stop_flag: Objeto compartilhado para controlar parada (dict com 'stop' key)
        user_id: ID do usuário para logging
        check_interval_minutes: Intervalo em minutos entre verificações das médias móveis
        enabled_assets: Lista de ativos habilitados
    """
    import sqlite3
    
    DB_PATH = 'cryptobot.db'
    if api_key and api_secret:
        # Criar cliente Binance
        client = Client(api_key, api_secret)
    else:
        load_dotenv()
        api_key = os.getenv("KEY_BINANCE")
        api_secret = os.getenv("SECRET_BINANCE")
        # Criar cliente Binance
        client = Client(api_key, api_secret)
    
    # Configurar recvWindow padrão para evitar erros de timestamp
    # O recvWindow será passado explicitamente nas chamadas de API que precisarem
    if hasattr(client, 'REQUEST_TIMEOUT'):
        # A biblioteca python-binance moderna suporta configuração de timeout
        pass
    
    # Sincronizar tempo com servidor Binance na inicialização
    try:
        server_time = client.get_server_time()
        server_timestamp = server_time['serverTime']
        local_timestamp = int(time.time() * 1000)
        offset = server_timestamp - local_timestamp
        if abs(offset) > 5000:
            print(f"Warning: Time offset detected: {offset}ms")
    except Exception as e:
        print(f"Error syncing time: {e}")
    
    # Use enabled assets if provided, otherwise use default
    if enabled_assets:
        ativos = enabled_assets
    else:
        ativos = ["BNBUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    intervalo = Client.KLINE_INTERVAL_30MINUTE
    
    # Buscar investment_amount para cada ativo do banco de dados
    asset_investment_amounts = {}
    if user_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT asset_symbol, investment_amount 
                FROM asset_settings 
                WHERE user_id = ?
            ''', (user_id,))
            for row in cursor.fetchall():
                asset_investment_amounts[row[0]] = row[1]
            conn.close()
        except Exception as e:
            print(f"Erro ao buscar investment_amount: {e}")
    
    while True:
        if stop_flag and stop_flag.get('stop', False):
            print(f"Bot parado para usuário {user_id}")
            break
        
        posicoes = {}
        
        # Verificar estado inicial de cada ativo
        for ativo in ativos:
            try:
                ticker = client.get_symbol_ticker(symbol=ativo)
                preco_atual = float(ticker["price"])
                is_totally_positioned, not_positioned = verificar_estado_inicial(client, ativo, preco_atual)
                posicoes[ativo] = (is_totally_positioned, not_positioned)
            except Exception as e:
                print(f"Erro ao obter posição inicial de {ativo}: {e}")
                continue
        
        # Processar cada ativo
        for ativo in ativos:
            if stop_flag and stop_flag.get('stop', False):
                break
                
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
                
                # Buscar investment_amount para este ativo
                investment_amount = asset_investment_amounts.get(ativo, 10.0)
                
                is_totally_positioned, status_message = estrategia_trading(
                    dados, ativo, client, is_totally_positioned, not_positioned, investment_amount
                )
                posicoes[ativo] = (is_totally_positioned, not_positioned)

                if status_message:
                    print(status_message)

                conta = client.get_account(recvWindow=60000)
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
        
        # Aguardar antes da próxima iteração (intervalo configurável)
        if not (stop_flag and stop_flag.get('stop', False)):
            check_interval_seconds = check_interval_minutes * 60
            print(f"Aguardando {check_interval_minutes} minutos antes da próxima verificação...")
            # Aguardar em intervalos de 5 segundos para verificar stop_flag frequentemente
            iterations = int(check_interval_seconds / 5)
            for _ in range(iterations):
                if stop_flag and stop_flag.get('stop', False):
                    break
                time.sleep(5)

def main():
    import sqlite3
    
    DB_PATH = 'cryptobot.db'
    load_dotenv()
    api_key = os.getenv("KEY_BINANCE")
    api_secret = os.getenv("SECRET_BINANCE")
    # Criar cliente Binance
    client = Client(api_key, api_secret)
    
    # O recvWindow agora é passado explicitamente nas chamadas de API que precisarem
    # Isso evita problemas de duplicação de parâmetros

    ativos = ["BNBUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    intervalo = Client.KLINE_INTERVAL_30MINUTE
    posicoes = {}
    
    # Buscar investment_amount para cada ativo do banco de dados (sem user_id, usar padrão)
    asset_investment_amounts = {}
    # Para função main() sem user_id, usar valor padrão de 10 USD para todos os ativos
    for ativo in ativos:
        asset_investment_amounts[ativo] = 10.0

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
            
            # Buscar investment_amount para este ativo
            investment_amount = asset_investment_amounts.get(ativo, 10.0)
            
            is_totally_positioned, status_message = estrategia_trading(
                dados, ativo, client, is_totally_positioned, not_positioned, investment_amount
            )
            posicoes[ativo] = (is_totally_positioned, not_positioned)

            if status_message:
                print(status_message)

            conta = client.get_account(recvWindow=60000)
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
