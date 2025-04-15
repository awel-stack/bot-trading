import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title='Bot Trading Dashboard', layout='wide')

st.title("📈 Dashboard del Bot de Trading en Vivo")

# Leer el archivo CSV
def cargar_datos():
    try:
        df = pd.read_csv("registro_bot.csv")
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    except:
        return pd.DataFrame(columns=["fecha", "accion", "probabilidad", "precio", "pnl", "resultado", "motivo"])

df = cargar_datos()

# ====================
# MÉTRICAS SIMPLES
# ====================
st.subheader("🔎 Resumen de decisiones")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de decisiones", len(df))
col2.metric("Operaciones BUY", (df['accion'] == 'buy').sum())
col3.metric("Operaciones SELL", (df['accion'] == 'sell').sum())
col4.metric("Operaciones HOLD", (df['accion'] == 'hold').sum())

# ====================
# MÉTRICAS DE RENDIMIENTO
# ====================
st.subheader("📊 Desempeño del Bot")
df_operaciones = df[df['pnl'].notna()]  # Solo operaciones con resultado
total_ops = len(df_operaciones)
ops_exitosas = len(df_operaciones[df_operaciones['resultado'].str.contains('✅')])
porcentaje_exito = round((ops_exitosas / total_ops) * 100, 2) if total_ops > 0 else 0
pnl_total = round(df_operaciones['pnl'].sum(), 2)
pnl_promedio = round(df_operaciones['pnl'].mean(), 2) if total_ops > 0 else 0
pnl_max = round(df_operaciones['pnl'].max(), 2) if total_ops > 0 else 0
pnl_min = round(df_operaciones['pnl'].min(), 2) if total_ops > 0 else 0

col5, col6, col7, col8 = st.columns(4)
col5.metric("🎯 % de aciertos", f"{porcentaje_exito}%")
col6.metric("💰 PnL total estimado", f"${pnl_total}")
col7.metric("📈 Promedio por operación", f"${pnl_promedio}")
col8.metric("🏁 Máx / Mín", f"${pnl_max} / ${pnl_min}")

# ====================
# HISTORIAL
# ====================
st.subheader("📋 Historial de decisiones")
st.dataframe(df.sort_values("fecha", ascending=False), use_container_width=True)

# ====================
# LÍNEA DE TIEMPO
# ====================
if not df.empty:
    st.subheader("🕒 Operaciones por hora")
    chart_data = df.groupby(df['fecha'].dt.floor('H'))['accion'].value_counts().unstack().fillna(0)
    st.line_chart(chart_data)

# ====================
# PNL ACUMULADO
# ====================
if not df_operaciones.empty:
    st.subheader("📉 Evolución del PnL acumulado")
    df_operaciones['pnl_acumulado'] = df_operaciones['pnl'].cumsum()
    st.line_chart(df_operaciones.set_index('fecha')['pnl_acumulado'])

# ====================
# AUTO-REFRESH
# ====================
st.caption("Este panel se refresca automáticamente cada 10 segundos.")
time.sleep(10)
st.rerun()