import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def backtest_ma(data, short_window=7, long_window=40, initial_cash=20):
    """
    Executa o backtesting da estratégia de médias móveis.
    
    Parâmetros:
    data (DataFrame): Dados históricos com a coluna 'Close'.
    short_window (int): Período para a média móvel curta (default=7).
    long_window (int): Período para a média móvel longa (default=40).
    initial_cash (float): Valor inicial em dólares para investir (default=20).
    
    Retorna:
    DataFrame contendo a evolução do valor da carteira para a estratégia e para o buy and hold.
    """
    df = data.copy()
    df['MA7'] = df['Close'].rolling(window=short_window).mean()
    df['MA40'] = df['Close'].rolling(window=long_window).mean()
    
    # Determina o primeiro dia em que ambos os indicadores estão disponíveis
    valid_start = df['MA40'].first_valid_index()
    if valid_start is None:
        # Não há dados suficientes para calcular as médias
        return pd.DataFrame()
    
    start_idx = df.index.get_loc(valid_start)
    
    # Inicializa as variáveis
    cash = initial_cash
    position = 0.0
    portfolio_values = []
    
    # Estratégia Buy and Hold: compra no dia de início válido
    buy_hold_shares = initial_cash / df['Close'].values[start_idx]
    buy_hold_values = []
    
    # Preenche os dias anteriores com o valor inicial (o backtesting começa somente após as médias serem calculadas)
    for i in range(start_idx):
        portfolio_values.append(initial_cash)
        buy_hold_values.append(buy_hold_shares * df['Close'].values[i])
    
    # No primeiro dia válido, se MA7 > MA40, compra imediatamente
    if df['MA7'].iat[start_idx] > df['MA40'].iat[start_idx]:
        position = cash / df['Close'].values[start_idx]
        cash = 0
    
    portfolio_value = cash + position * df['Close'].values[start_idx]
    portfolio_values.append(portfolio_value)
    buy_hold_values.append(buy_hold_shares * df['Close'].values[start_idx])
    
    # Simula a partir do dia seguinte ao de início válido
    for i in range(start_idx + 1, len(df)):
        # Calcula os sinais apenas se ambos os indicadores estiverem disponíveis
        if pd.notna(df['MA7'].iat[i]) and pd.notna(df['MA7'].iat[i - 1]):
            prev_diff = df['MA7'].iat[i - 1] - df['MA40'].iat[i - 1]
            curr_diff = df['MA7'].iat[i] - df['MA40'].iat[i]
            close_price = df['Close'].values[i]
            
            # Sinal de COMPRA: se não estiver investido e ocorrer o cruzamento de alta
            if position == 0 and prev_diff <= 0 and curr_diff > 0:
                position = cash / close_price
                cash = 0
            # Sinal de VENDA: se estiver investido e ocorrer o cruzamento de baixa
            elif position > 0 and prev_diff >= 0 and curr_diff < 0:
                cash = position * close_price
                position = 0
        
        # Atualiza o valor da carteira
        portfolio_value = cash + position * df['Close'].values[i]
        portfolio_values.append(portfolio_value)
        
        # Estratégia Buy and Hold permanece comprada desde o início válido
        buy_hold_value = buy_hold_shares * df['Close'].values[i]
        buy_hold_values.append(buy_hold_value)
    
    result = pd.DataFrame({'Strategy': portfolio_values, 'BuyHold': buy_hold_values}, index=df.index)
    return result

def main():
    # Define os ativos e seus tickers no yfinance
    tickers = {
        'XRP': 'XRP-USD',
        'ETH': 'ETH-USD',
        'BNB': 'BNB-USD',
        'BTC': 'BTC-USD',
        'SOL': 'SOL-USD'
    }
    
    # Período para o backtesting
    start_date = '2020-01-01'
    end_date = pd.Timestamp.today().strftime('%Y-%m-%d')
    
    for asset, ticker in tickers.items():
        print(f"Baixando dados para {asset} ({ticker})...")
        data = yf.download(ticker, start=start_date, end=end_date)
        
        if data.empty:
            print(f"Nenhum dado encontrado para {asset}.")
            continue
        
        result = backtest_ma(data)
        
        if not result.empty:
            plt.figure(figsize=(10, 5))
            plt.plot(result.index, result['Strategy'], label='Estratégia MA')
            plt.plot(result.index, result['BuyHold'], label='Buy and Hold')
            plt.title(f"Backtesting de Médias Móveis - {asset}")
            plt.xlabel('Data')
            plt.ylabel('Valor da Carteira (US$)')
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()
if __name__ == "__main__":
    main()
