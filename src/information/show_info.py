def create_info_box(symbol, min_qty, max_qty, step_size, current_price):
    # Display asset information in a formatted box
    print(f"\n╔═════════════════════════════════ {symbol} ════════════════════════════════╗")
    print(f" Quantidade mínima: {min_qty}")
    print(f" Quantidade máxima: {max_qty}")
    print(f" Passo: {step_size}")
    print(f" Preço atual: {current_price}")
    print("╟──────────────────────────────────────────────────────────────────────────╢")

def print_moving_averages(rapida, lenta):
    # Print the latest moving averages
    print(f" Última média rápida: {rapida:.3f} | Última média lenta: {lenta:.3f}               ")

def print_rsi(rsi):
    # Print the current RSI
    print(f" RSI Atual: {rsi:.2f}                                               ")

def print_position(ativo, quantidade, valor_usdt, show_usdt):
    # Print the current position details
    if show_usdt:
        print(f" Valor em USDT: {valor_usdt:.2f}")
    else:
        print(f" Quantidade: {quantidade}")
        print(f" Valor em USDT: {float(quantidade):.2f}")
        return


