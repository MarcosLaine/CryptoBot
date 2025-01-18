def verificar_estado_inicial(client, ativo, preco_atual):
    """
    Verifica o estado inicial de posição com base no saldo atual e preço do ativo.

    Parâmetros:
        client (Client): Cliente Binance.
        ativo (str): Símbolo do ativo (e.g., 'BNB').
        preco_atual (float): Preço atual do ativo.

    Retorna:
        tuple: Estados de posição inicial (is_totally_positioned, is_partially_positioned, not_positioned).
    """
    # Obtém saldo do ativo
    conta = client.get_account()
    saldo_disponivel = 0
    for item in conta['balances']:
        if item['asset'] == ativo.split("USDT")[0]:
            saldo_disponivel = float(item['free'])
            break

    # Calcula o valor atual em USDT
    valor_em_usdt = saldo_disponivel * preco_atual

    # Determina o estado de posição
    if valor_em_usdt >= 15:
        return True, False, False  # Totalmente posicionado
    elif 4.99 <= valor_em_usdt < 15:
        return False, True, False  # Parcialmente posicionado
    else:
        return False, False, True  # Não posicionado
