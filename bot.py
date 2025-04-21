import ccxt
import pandas as pd
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import joblib

print("🚀 Bot iniciado correctamente")

# Cargar variables de entorno
load_dotenv()

# Configuración de API Bybit
exchange = ccxt.bybit({
    'apiKey': os.getenv('rO4Hf4hxsj2thBWxVg'),
    'secret': os.getenv('4ahhlHTAV49OUOfv5zaG6bWLxjcwG2avcdXY'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot'  # puedes cambiar a 'future' si quieres futuros
    }
})

# Conexión a Google Sheets
try:
    print("🔐 Conectando a Google Sheets...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1FN3NhAO2DO6Lg5f-OMJ8inOcua2K-Zu1LVQihPXlKls").sheet1
    print("✅ Conectado a Google Sheets")
except Exception as e:
    print(f"💥 Error al conectar con Google Sheets: {e}")
    exit()

# Cargar modelo
try:
    modelo = joblib.load("modelo_ia.pkl")
    print("✅ Modelo cargado")
except Exception as e:
    print(f"💥 Error cargando modelo IA: {e}")
    exit()

# Obtener datos de mercado
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
    print(f"📊 Probabilidad de subida: {prob:.2f}")

    if ultima['ema50'] > ultima['ema200'] and prob > 0.7:
        return "buy", prob, ultima['close']
    elif ultima['ema50'] < ultima['ema200'] and prob > 0.7:
        return "sell", prob, ultima['close']
    return "hold", prob, ultima['close']

# Guardar decisión en Google Sheets
def guardar_en_sheet(decision, prob, precio):
    try:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([ahora, decision, round(prob, 4), round(precio, 2), "", "", "Paper trading"])
        print(f"📝 Se guardó la decisión '{decision}' con probabilidad {prob:.2f} a precio {precio}")
    except Exception as e:
        print(f"⚠️ No se pudo guardar en Google Sheets: {e}")

# Bucle principal
while True:
    try:
        print(f"\n🕒 Análisis iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        df = obtener_datos()
        decision, prob, precio = tomar_decision(df)
        guardar_en_sheet(decision, prob, precio)
    except Exception as e:
        print(f"💥 Error general del bot: {e}")

    time.sleep(600)  # Espera 10 minutos


