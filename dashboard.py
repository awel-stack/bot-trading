import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title='Bot Trading Dashboard', layout='wide')

st.title("📈 Dashboard del Bot de Trading en Vivo")

# Leer los datos
def cargar_datos():
    try:
        df = pd.read_csv("registro_bot.csv")
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    except:
        return pd.DataFrame(columns=["fecha", "accion", "probabilidad", "precio", "pnl", "motivo"])

df = cargar_datos()

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de decisiones", len(df))
col2.metric("Operaciones BUY", (df['accion'] == 'buy').sum())
col3.metric("Operaciones SELL", (df['accion'] == 'sell').sum())
col4.metric("Operaciones HOLD", (df['accion'] == 'hold').sum())

# Tabla con historial
st.subheader("📋 Historial de decisiones")
st.dataframe(df.sort_values("fecha", ascending=False), use_container_width=True)

# Gráfica de acciones a lo largo del tiempo
if not df.empty:
    st.subheader("📊 Línea de tiempo de operaciones")
    chart_data = df.groupby(df['fecha'].dt.floor('H'))['accion'].value_counts().unstack().fillna(0)
    st.line_chart(chart_data)

# Refrescar automáticamente cada 10 segundos
st.caption("Este panel se refresca automáticamente cada 10 segundos.")
time.sleep(10)
st.rerun()
