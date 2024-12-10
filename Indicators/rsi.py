def calcular_rsi(dados, periodo=14):
    """
    Calcula o Índice de Força Relativa (RSI).

    Parâmetros:
        dados (DataFrame): DataFrame com a coluna 'preco_fechamento'.
        periodo (int): Período para cálculo do RSI.

    Retorna:
        DataFrame: Dados com coluna 'rsi'.
    """
    delta = dados['preco_fechamento'].diff()
    ganhos = delta.where(delta > 0, 0)
    perdas = -delta.where(delta < 0, 0)
    media_ganhos = ganhos.rolling(window=periodo).mean()
    media_perdas = perdas.rolling(window=periodo).mean()
    rs = media_ganhos / media_perdas
    dados['rsi'] = 100 - (100 / (1 + rs))
    return dados
