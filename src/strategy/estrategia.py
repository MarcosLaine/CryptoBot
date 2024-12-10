import math

def estrategia_trading(dados, ativo, client, is_totally_positioned, is_partially_positioned, not_positioned):
    """
    Executa lógica de compra e venda baseada em RSI e médias móveis.

    Parâmetros:
        dados (DataFrame): Dados com colunas 'media_curta', 'media_longa', e 'rsi'.
        ativo (str): Símbolo do ativo.
        client (Client): Cliente Binance.
        is_totally_positioned, is_partially_positioned, not_positioned (bool): Estados de posição.

    Retorna:
        tuple: Estados atualizados de posição e mensagem de status.
    """
    ultima_media_curta = dados['media_curta'].iloc[-1]
    ultima_media_longa = dados['media_longa'].iloc[-1]
    ultimo_rsi = dados['rsi'].iloc[-1]

    # Preço atual
    ticker = client.get_symbol_ticker(symbol=ativo)
    preco_atual = float(ticker['price'])

    # Quantidades
    quantidade_total = 20 / preco_atual
    quantidade_parcial = 10 / preco_atual

    # Ajustar precisão
    symbol_info = client.get_symbol_info(ativo)
    lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
    step_size = float(lot_size_filter['stepSize'])
    min_qty = float(lot_size_filter['minQty'])
    precision = int(round(-math.log(step_size, 10)))
    quantidade_total = max(round(quantidade_total, precision), min_qty)
    quantidade_parcial = max(round(quantidade_parcial, precision), min_qty)


    # Get current asset balance
    conta = client.get_account()
    saldo_disponivel = 0
    for item in conta['balances']:
        if item['asset'] == ativo.split("USDT")[0]:
            saldo_disponivel = float(item['free'])
            break

    # Calculate current value in USD
    valor_em_usdt = saldo_disponivel * preco_atual
    
    if ultimo_rsi < 70 or ultimo_rsi > 30:
        if ultima_media_curta > ultima_media_longa:
            if is_partially_positioned:
                return is_totally_positioned, is_partially_positioned, not_positioned, " Não compra pois já está parcialmente posicionado" #Não compra pois já está parcialmente posicionado
            if not_positioned or valor_em_usdt < 5:
                client.create_order(symbol=ativo, side="BUY", type="MARKET", quantity=f"{quantidade_parcial:.{precision}f}")
                return False, True, False, " Compra parcial realizada (parcialmente posicionado agora)" #Compra parcial realizada
    # Condições de Compra
    if ultimo_rsi <= 30:
        if ultima_media_curta < ultima_media_longa: #RSI abaixo e media curta abaixo da media longa
            if is_partially_positioned:
                return is_totally_positioned, is_partially_positioned, not_positioned, " Não compra pois já está parcialmente posicionado" #Não compra pois já está parcialmente posicionado
            if not_positioned and valor_em_usdt < 5:
                client.create_order(symbol=ativo, side="BUY", type="MARKET", quantity=f"{quantidade_parcial:.{precision}f}")
                return False, True, False, " Compra parcial realizada (parcialmente posicionado agora)"
            if is_totally_positioned:
                client.create_order(symbol=ativo, side="SELL", type="MARKET", quantity=f"{quantidade_parcial:.{precision}f}")
                return False, True, False, " Venda parcial realizada (parcialmente posicionado agora)" #Venda parcial realizada
        elif ultima_media_longa < ultima_media_curta: #RSI abaixo e media curta acima da media longa
            if is_partially_positioned and valor_em_usdt < 15:
                client.create_order(symbol=ativo, side="BUY", type="MARKET", quantity=f"{quantidade_parcial:.{precision}f}")
                return True, False, False, " Compra adicional realizada (totalmente posicionado agora)" #Compra adicional realizada
            if not_positioned:
                client.create_order(symbol=ativo, side="BUY", type="MARKET", quantity=f"{quantidade_total:.{precision}f}")
                return True, False, False, " Compra total realizada (totalmente posicionado agora)" #Compra total realizada

    # Condições de Venda
    elif ultimo_rsi >= 70:
        if ultima_media_curta < ultima_media_longa: #RSI acima e media curta abaixo da media longa
            if is_partially_positioned and valor_em_usdt >= 6:
                client.create_order(symbol=ativo, side="SELL", type="MARKET", quantity=f"{saldo_disponivel:.{precision}f}")
                return False, False, True, " Venda total realizada (não posicionado agora)   " #Venda total realizada
            if is_totally_positioned:
                client.create_order(symbol=ativo, side="SELL", type="MARKET", quantity=f"{quantidade_total:.{precision}f}")
                return False, False, True, " Venda total realizada (não posicionado agora)" #venda total realizada
        elif ultima_media_longa < ultima_media_curta: #RSI acima e media curta acima da media longa
            if is_partially_positioned and valor_em_usdt >= 6 and valor_em_usdt < 15:
                return False, True, False, " Não vende pois já está parcialmente posicionado" #Não vende pois já está parcialmente posicionado
            if is_totally_positioned:
                client.create_order(symbol=ativo, side="SELL", type="MARKET", quantity=f"{quantidade_parcial:.{precision}f}")
                return False, True, False, " Venda parcial realizada (parcialmente posicionado agora)" #venda parcial realizada
            if not_positioned:
                client.create_order(symbol=ativo, side="BUY", type="MARKET", quantity=f"{quantidade_parcial:.{precision}f}")
                return False, True, False, " Compra parcial realizada (parcialmente posicionado agora)" #compra parcial realizada

    return is_totally_positioned, is_partially_positioned, not_positioned, None # Não faz nada
