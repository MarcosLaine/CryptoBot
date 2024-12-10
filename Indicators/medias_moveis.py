def calcular_medias_moveis(dados, janela_curta=7, janela_longa=40):
    """
    Calcula médias móveis de curto e longo prazo.

    Parâmetros:
        dados (DataFrame): DataFrame com a coluna 'preco_fechamento'.
        janela_curta (int): Período para média móvel curta.
        janela_longa (int): Período para média móvel longa.

    Retorna:
        DataFrame: Dados com colunas 'media_curta' e 'media_longa'.
    """
    dados['media_curta'] = dados['preco_fechamento'].rolling(window=janela_curta).mean()
    dados['media_longa'] = dados['preco_fechamento'].rolling(window=janela_longa).mean()
    return dados