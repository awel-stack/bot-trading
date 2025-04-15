import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

exchange = ccxt.binance({
    'apiKey': os.getenv('API_KEY'),
    'secret': os.getenv('API_SECRET'),
})

# Verificar acceso a cuenta
balance = exchange.fetch_balance()
print(balance['total'])
