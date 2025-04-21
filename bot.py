import ccxt
import pandas as pd
import joblib
import os
import time
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# =========================
# CONEXIÓN A GOOGLE SHEETS
# =========================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("4ahhlHTAV49OUOfv5zaG6bWLxjcwG2avcdXY").sheet1

# =========================
# CONEXIÓN A BYBIT (Paper Trading con CCXT)
# =========================
exchange = ccxt.bybit({
    'apiKey': os.getenv("rO4Hf4hxsj2thBWxVg"),
    'secret': os.getenv("API_SECRET"),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'  # o 'spot' si prefieres
    }
})

# =========================
# CARGAR MODELO DE IA
# =========================
modelo = joblib.load("modelo_ia.pkl")

# =========================
# FUNCIÓN: OBTENER DATOS DE MERCADO
# =========================
def obtener_datos():
    velas = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=200)
    df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['ema50'] = df['close'].ewm(span=50).mean()
    df['ema200'] = df['close'].ewm(span=200).mean()

    # RSI
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

# =========================
# FUNCIÓN: TOMAR DECISIÓN
# =========================
def tomar_decision(df):
    ultima = df.iloc[-1]
    X = pd.DataFrame([{
        'ema50': ultima['ema50'],
        'ema200': ultima['ema200'],
        'rsi': ultima['rsi'],
        'macd': ultima['macd']
    }])
    prob = modelo.predict_proba(X)[0][1]

    if ultima['ema50'] > ultima['ema200'] and prob > 0.7:
        return "buy", prob, "Cruce EMA + IA alta"
    elif ultima['ema50'] < ultima['ema200'] and prob > 0.7:
        return "sell", prob, "Cruce EMA negativo + IA alta"
    else:
        return "hold", prob, "Condición neutral"

# =========================
# FUNCIÓN: REGISTRAR EN GOOGLE SHEETS
# =========================
def registrar_decision(fecha, accion, probabilidad, precio, motivo):
    fila = [fecha, accion, round(probabilidad, 4), precio, "", "", motivo]
    sheet.append_row(fila)

# =========================
# LOOP PRINCIPAL DEL BOT
# =========================
while True:
    try:
        print(f"\n🕒 Análisis iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        df = obtener_datos()
        decision, prob, motivo = tomar_decision(df)
        precio_actual = df.iloc[-1]['close']

        print(f"📊 Decisión del bot: {decision.upper()} con probabilidad {prob:.2f}")
        registrar_decision(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            decision,
            prob,
            precio_actual,
            motivo
        )

    except Exception as e:
        print(f"⚠️ Error: {e}")

    print("⏱️ Esperando 10 minutos para nueva señal...\n")
    time.sleep(600)

