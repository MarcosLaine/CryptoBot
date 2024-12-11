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
    try:
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
        
        # Função auxiliar para executar ordens com tratamento de erro
        def execute_order(side, quantity):
            try:
                client.create_order(
                    symbol=ativo, 
                    side=side, 
                    type="MARKET", 
                    quantity=f"{quantity:.{precision}f}"
                )
                return True
            except Exception as e:
                print(f" Erro ao executar ordem {side}: {str(e)}")
                return False

        # Condições de Compra se está entre 30 e 70
        if ultimo_rsi < 70 or ultimo_rsi > 30:
            if ultima_media_curta > ultima_media_longa:
                if is_partially_positioned:
                    return is_totally_positioned, is_partially_positioned, not_positioned, " Não compra pois já está parcialmente posicionado"
                if not_positioned or valor_em_usdt < 5:
                    if execute_order("BUY", quantidade_parcial):
                        return False, True, False, " Compra parcial realizada (parcialmente posicionado agora)"
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na compra parcial"

        # Condições de Compra
        if ultimo_rsi <= 30:
            if ultima_media_curta < ultima_media_longa: #RSI abaixo e media curta abaixo da media longa
                if is_partially_positioned:
                    return is_totally_positioned, is_partially_positioned, not_positioned, " Não compra pois já está parcialmente posicionado" #Não compra pois já está parcialmente posicionado
                if not_positioned and valor_em_usdt < 5:
                    if execute_order("BUY", quantidade_parcial):
                        return False, True, False, " Compra parcial realizada (parcialmente posicionado agora)"
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na compra parcial"
                if is_totally_positioned:
                    if execute_order("SELL", quantidade_parcial):
                        return False, True, False, " Venda parcial realizada (parcialmente posicionado agora)" #Venda parcial realizada
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na venda parcial"
            elif ultima_media_longa < ultima_media_curta: #RSI abaixo e media curta acima da media longa
                if is_partially_positioned and valor_em_usdt < 15:
                    if execute_order("BUY", quantidade_parcial):
                        return True, False, False, " Compra adicional realizada (totalmente posicionado agora)" #Compra adicional realizada
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na compra adicional"
                if not_positioned:
                    if execute_order("BUY", quantidade_total):
                        return True, False, False, " Compra total realizada (totalmente posicionado agora)" #Compra total realizada
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na compra total"

        # Condições de Venda
        elif ultimo_rsi >= 70:
            if ultima_media_curta < ultima_media_longa: #RSI acima e media curta abaixo da media longa
                if is_partially_positioned and valor_em_usdt >= 6:
                    quantidade_venda = math.floor(saldo_disponivel * (10 ** precision)) / (10 ** precision) #arredonda para baixo
                    if execute_order("SELL", f"{quantidade_venda:.{precision}f}"):
                        return False, False, True, " Venda total realizada (não posicionado agora)   " #Venda total realizada
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na venda total"
                if is_totally_positioned:
                    quantidade_venda = math.floor(saldo_disponivel * (10 ** precision)) / (10 ** precision) #arredonda para baixo
                    if execute_order("SELL", f"{quantidade_venda:.{precision}f}"):
                        return False, False, True, " Venda total realizada (não posicionado agora)" #venda total realizada
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na venda total"
            elif ultima_media_longa < ultima_media_curta: #RSI acima e media curta acima da media longa
                if is_partially_positioned and valor_em_usdt >= 6 and valor_em_usdt < 15:
                    return False, True, False, " Não vende pois já está parcialmente posicionado" #Não vende pois já está parcialmente posicionado
                if is_totally_positioned:
                    if execute_order("SELL", quantidade_parcial):
                        return False, True, False, " Venda parcial realizada (parcialmente posicionado agora)" #venda parcial realizada
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na venda parcial"
                if not_positioned:
                    if execute_order("BUY", quantidade_parcial):
                        return False, True, False, " Compra parcial realizada (parcialmente posicionado agora)" #compra parcial realizada
                    else:
                        return is_totally_positioned, is_partially_positioned, not_positioned, " Falha na compra parcial"

        return is_totally_positioned, is_partially_positioned, not_positioned, None # Não faz nada

    except Exception as e:
        print(f" Erro na estratégia de trading: {str(e)}")
        return is_totally_positioned, is_partially_positioned, not_positioned, f" Erro: {str(e)}"
