import ccxt
import pandas as pd
import joblib
import os
import time
from dotenv import load_dotenv

# Cargar archivo .env con las claves API
load_dotenv()

# Cargar el modelo de IA
modelo = joblib.load("modelo_ia.pkl")

# Conectar con Binance
exchange = ccxt.binance({
    'apiKey': os.getenv('API_KEY'),
    'secret': os.getenv('API_SECRET'),
    'enableRateLimit': True
})

# Obtener datos en vivo de Binance
def obtener_datos():
    velas = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=200)
    df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['ema50'] = df['close'].ewm(span=50).mean()
    df['ema200'] = df['close'].ewm(span=200).mean()
    
    # RSI manual
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26

    return df.dropna()

# Tomar decisión con IA
def tomar_decision(df):
    ultima = df.iloc[-1]
    X = pd.DataFrame([{
    'ema50': ultima['ema50'],
    'ema200': ultima['ema200'],
    'rsi': ultima['rsi'],
    'macd': ultima['macd']
}])
    prob = modelo.predict_proba(X)[0][1]
    print(f"📊 Probabilidad de que suba: {prob:.2f}")

    if ultima['ema50'] > ultima['ema200'] and prob > 0.7:
        return "buy"
    elif ultima['ema50'] < ultima['ema200'] and prob > 0.7:
        return "sell"
    return "hold"

# Simular orden
def ejecutar_orden(tipo):
    monto = 0.001  # simulación, no es real
    if tipo == "buy":
        print(f"🟢 [SIMULACIÓN] Habríamos comprado {monto} BTC ✅")
    elif tipo == "sell":
        print(f"🔴 [SIMULACIÓN] Habríamos vendido {monto} BTC ✅")

# Bucle principal del bot
from datetime import datetime

while True:
    try:
        print(f"\n🕒 Análisis iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔍 Analizando el mercado...")
        df = obtener_datos()
        decision = tomar_decision(df)
        if decision != "hold":
            ejecutar_orden(decision)
        else:
            print("⏸️ No se ejecutó ninguna orden. Se decidió HOLD.")
    except Exception as e:
        print(f"⚠️ Error: {e}")

    print("⏱️ Esperando 10 minutos para nueva señal...\n")
    time.sleep(600)  # 600 segundos = 10 minutos
