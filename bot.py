import ccxt
import time
import pandas as pd
from datetime import datetime
from joblib import load
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

# Cargar variables de entorno
load_dotenv()
POSTGRES_URL = os.getenv("POSTGRES_URL")
engine = create_engine(POSTGRES_URL)

# Cargar modelo ML
modelo = load("modelo_ia.pkl")

# Conectar a Bybit (futures)
exchange = ccxt.bybit({
    "apiKey": os.getenv("BYBIT_API_KEY"),
    "secret": os.getenv("BYBIT_API_SECRET"),
    "enableRateLimit": True,
    "options": {"defaultType": "future"}  # Usar el mercado de futuros
})

print("\n🚀 Bot iniciado correctamente")

def obtener_datos():
    print("✅ Obteniendo datos de Bybit Futures...")
    velas = exchange.fetch_ohlcv("BTC/USDT:USDT", timeframe="5m", limit=50)  # Futuros
    df = pd.DataFrame(velas, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df["ma_20"] = df["close"].rolling(window=20).mean()
    df["ma_50"] = df["close"].rolling(window=50).mean()
    df.dropna(inplace=True)
    return df

def hacer_prediccion(df):
    X = df[["close", "ma_20", "ma_50"]].copy()
    prediccion = modelo.predict(X.tail(1))
    probas = modelo.predict_proba(X.tail(1))
    return prediccion[0], max(probas[0])

def registrar_decision(accion, probabilidad, precio, motivo):
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO decisiones (fecha, accion, probabilidad, precio, pnl, resultado, motivo)
                    VALUES (now(), :accion, :probabilidad, :precio, :pnl, :resultado, :motivo)
                """),
                {
                    "accion": accion,
                    "probabilidad": round(probabilidad, 4),
                    "precio": precio,
                    "pnl": 0,
                    "resultado": None,
                    "motivo": motivo
                }
            )
        print(f"✅ Decisión registrada: {accion.upper()} con probabilidad {probabilidad:.2f}")
    except Exception as e:
        print(f"❌ Error al registrar en base de datos: {e}")

def main():
    while True:
        print("\n🕒 Análisis iniciado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            df = obtener_datos()
            prediccion, probabilidad = hacer_prediccion(df)
            precio_actual = df["close"].iloc[-1]
            registrar_decision(prediccion, probabilidad, precio_actual, "Cruce de medias móviles")
        except Exception as e:
            print("⚠️ Error en ejecución:", e)

        time.sleep(60)  # Esperar 1 minuto entre análisis

if __name__ == "__main__":
    try:
        print("🔐 Conectando a Bybit Futures...")
        main()
    except KeyboardInterrupt:
        print("🛑 Bot detenido manualmente")



