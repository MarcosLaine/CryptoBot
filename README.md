# CryptoBot

CryptoBot is a powerful and flexible bot designed to help you track and manage cryptocurrency investments. It provides real-time data, alerts, and analytics to help you make informed decisions.

## Features

- Real-time cryptocurrency price tracking
- Customizable alerts for price changes
- Portfolio management and analytics
- Integration with popular exchanges

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have installed [Python 3.x](https://www.python.org/downloads/)
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

   ```bash
   pip install python-binance
   pip install pandas
   ```

## Configuration

1. **Set up your API keys:**

   - Obtain API keys from your preferred cryptocurrency exchange.
   - Create a `.env` file in the root directory and add your API keys:

     ```plaintext
     EXCHANGE_API_KEY=your_api_key
     EXCHANGE_API_SECRET=your_api_secret
     ```

## Usage

1. **Run the bot:**

   ```bash
   python run_all_bots.py
   ```

2. **Monitor the console for real-time updates and alerts.**

## Contact

If you have any questions or feedback, feel free to reach out at [marcospslaine@gmail.com].

