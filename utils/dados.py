import pandas as pd
from binance.client import Client

def obter_dados_historicos(client, simbolo, intervalo, limite=1000):
    """
    Obtém dados históricos de preços.

    Parâmetros:
        client (Client): Cliente Binance.
        simbolo (str): Símbolo do ativo (e.g., 'BNBUSDT').
        intervalo (str): Intervalo dos candles.
        limite (int): Número de registros a serem obtidos.

    Retorna:
        DataFrame: Dados de preços.
    """
    candles = client.get_klines(symbol=simbolo, interval=intervalo, limit=limite)
    dados = pd.DataFrame(candles, columns=[
        'tempo_abertura', 'preco_abertura', 'preco_maximo', 'preco_minimo',
        'preco_fechamento', 'volume', 'tempo_fechamento', 'moedas_negociadas',
        'numero_trades', 'volume_ativo_base_compra', 'volume_cotacao', '-'
    ])
    dados = dados[['preco_fechamento', 'tempo_fechamento']]
    dados['preco_fechamento'] = dados['preco_fechamento'].astype(float)
    dados['tempo_fechamento'] = pd.to_datetime(dados['tempo_fechamento'], unit='ms')
    return dados
