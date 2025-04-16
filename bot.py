import ccxt
import pandas as pd
import joblib
import os
import time
from dotenv import load_dotenv
from datetime import datetime
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

# Conectarse a Google Sheets usando credenciales desde variable de entorno
def conectar_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1Otzxl7E7RKA0PGEvcpUPD3Tj1E60H_aNbiu_Oe4Hlj0").sheet1  # <--- Reemplaza con tu ID real
    return sheet

# Registrar operación en Google Sheets
def registrar_operacion(fecha, accion, prob, precio, motivo):
    sheet = conectar_sheet()
    nueva_fila = [fecha, accion, round(prob, 4), round(precio, 2), "", "", motivo]
    sheet.append_row(nueva_fila)

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
        return "buy", prob, ultima['close'], "Cruce alcista + alta probabilidad"
    elif ultima['ema50'] < ultima['ema200'] and prob > 0.7:
        return "sell", prob, ultima['close'], "Cruce bajista + alta probabilidad"
    return "hold", prob, ultima['close'], "Condiciones no favorables"

# Simular orden
def ejecutar_orden(tipo):
    monto = 0.001  # simulación, no es real
    if tipo == "buy":
        print(f"🟢 [SIMULACIÓN] Habríamos comprado {monto} BTC ✅")
    elif tipo == "sell":
        print(f"🔴 [SIMULACIÓN] Habríamos vendido {monto} BTC ✅")

# Bucle principal del bot
while True:
    try:
        print(f"\n🕒 Análisis iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔍 Analizando el mercado...")
        df = obtener_datos()
        decision, prob, precio, motivo = tomar_decision(df)

        if decision != "hold":
            ejecutar_orden(decision)
            registrar_operacion(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), decision, prob, precio, motivo)
        else:
            print("⏸️ No se ejecutó ninguna orden. Se decidió HOLD.")

    except Exception as e:
        print(f"⚠️ Error: {e}")

    print("⏱️ Esperando 10 minutos para nueva señal...\n")
    time.sleep(600)  # 600 segundos = 10 minutos
