import math

def estrategia_trading(dados, ativo, client, is_totally_positioned, not_positioned, investment_amount=10.0):
    """
        Executa lógica de compra e venda baseada em médias móveis, sem utilizar o RSI.


    Parâmetros:
        dados (DataFrame): Dados com colunas 'media_curta', 'media_longa', e 'rsi'.
        ativo (str): Símbolo do ativo.
        client (Client): Cliente Binance.
        is_totally_positioned, not_positioned (bool): Estados de posição.
        investment_amount (float): Valor em USDT para investir por operação (padrão: 10.0).


    Retorna:
        tuple: Estados atualizados de posição e mensagem de status.
    """
    ultima_media_curta = dados['media_curta'].iloc[-1]
    ultima_media_longa = dados['media_longa'].iloc[-1]

    # Preço atual
    ticker = client.get_symbol_ticker(symbol=ativo)
    preco_atual = float(ticker['price'])

    # Quantidades - usar o investment_amount configurado pelo usuário
    # Se investment_amount for 0, usar valor padrão de 10 USD
    amount_to_invest = investment_amount if investment_amount > 0 else 10.0
    quantidade_total = amount_to_invest / preco_atual

    # Ajustar precisão
    symbol_info = client.get_symbol_info(ativo)
    lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
    step_size = float(lot_size_filter['stepSize'])
    min_qty = float(lot_size_filter['minQty'])
    precision = int(round(-math.log(step_size, 10)))
    quantidade_total = max(round(quantidade_total, precision), min_qty)

    # Get current asset balance
    conta = client.get_account(recvWindow=60000)
    saldo_disponivel = 0
    for item in conta['balances']:
        if item['asset'] == ativo.split("USDT")[0]:
            saldo_disponivel = float(item['free'])
            break

    # Calculate current value in USD
    valor_em_usdt = saldo_disponivel * preco_atual
    
    # Estratégia baseada apenas em médias móveis:
    # Se a média curta for maior que a média longa => sinal de compra
    if ultima_media_curta > ultima_media_longa:
        if not_positioned or valor_em_usdt < 5:
            client.create_order(
                symbol=ativo, 
                side="BUY", 
                type="MARKET", 
                quantity=f"{quantidade_total:.{precision}f}",
                recvWindow=60000
            )
            is_totally_positioned = True
            return is_totally_positioned, " Compra realizada"
    


    # Se a média curta for menor ou igual que a média longa e o ativo estiver posicionado, venda
    if ultima_media_curta <= ultima_media_longa and (is_totally_positioned):
        client.create_order(
            symbol=ativo, 
            side="SELL", 
            type="MARKET", 
            quantity=f"{saldo_disponivel:.{precision}f}",
            recvWindow=60000
        )
        is_totally_positioned = False
        return is_totally_positioned, " Venda realizada"

    return is_totally_positioned, " Nenhuma ação realizada"
