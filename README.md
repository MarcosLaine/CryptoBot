# CryptoBot

CryptoBot is a powerful and flexible bot designed to help you track and manage cryptocurrency investments. It provides real-time data, alerts, and analytics to help you make informed decisions.

## Features

- Real-time cryptocurrency price tracking
- Customizable alerts for price changes
- Portfolio management and analytics
- Integration with popular exchanges
- Automated trading strategies based on RSI and moving averages

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have installed [Anaconda Python 3.x](https://www.anaconda.com/download/success)
- You have a working internet connection
- You have an account on a supported cryptocurrency exchange (if applicable)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/MarcosLaine/CryptoBot.git
   cd CryptoBot
   ```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages:**

   Open the Anaconda Prompt and install the required packages:

   ```bash
   pip install python-binance pandas
   ```

## Configuration

1. **Set up your API keys:**

   - Obtain API keys from your preferred cryptocurrency exchange.
   - Create a `.env` file in the root directory and add your API keys:

     ```plaintext
     EXCHANGE_API_KEY= "your_api_key"
     EXCHANGE_API_SECRET= "your_api_secret"
     ```

## Usage

1. **Run the bot:**

   Make sure you are using the Anaconda Interpreter

   ```bash
   python main.py
   ```

2. **Monitor the console for real-time updates and alerts.**

## Project Structure

- **main.py**: Main script to run the bot.
- **src/strategy/estrategia.py**: Contains trading strategy logic.
- **src/information/exibir_info.py**: Handles information display.
- **utils/dados.py**: Utility functions for data handling.
- **Indicadores/**: Contains indicator calculation modules.

## Contact

If you have any questions or feedback, feel free to reach out at [marcospslaine@gmail.com].

