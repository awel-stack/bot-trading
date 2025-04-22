import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title='Bot Trading Dashboard', layout='wide')
st.title("📈 Dashboard del Bot de Trading en Vivo")

# Configurar conexión a Google Sheets desde st.secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1FN3NhAO2DO6Lg5f-OMJ8inOcua2K-Zu1LVQihPXlKls").sheet1  # Tu Sheet ID

# Leer los datos desde Google Sheets (con caché de 60 segundos)
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        registros = sheet.get_all_records()
        df = pd.DataFrame(registros)
        df.columns = df.columns.astype(str).str.strip().str.lower()

        if 'fecha' not in df.columns:
            raise KeyError("La columna 'fecha' no está presente en el archivo de Google Sheets.")

        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df[df['fecha'].notnull()]

        return df

    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(columns=["fecha", "accion", "probabilidad", "precio", "pnl", "resultado", "motivo"])

df = cargar_datos()

# Métricas principales
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de decisiones", len(df))
col2.metric("Operaciones BUY", (df['accion'] == 'buy').sum())
col3.metric("Operaciones SELL", (df['accion'] == 'sell').sum())
col4.metric("Operaciones HOLD", (df['accion'] == 'hold').sum())

# Nueva métrica: efectividad del bot
if 'resultado' in df.columns and not df['resultado'].isnull().all():
    total_validas = df['resultado'].isin(['ganancia', 'pérdida']).sum()
    aciertos = (df['resultado'] == 'ganancia').sum()
    efectividad = (aciertos / total_validas * 100) if total_validas > 0 else 0
    col5.metric("🎯 Efectividad del Bot", f"{efectividad:.1f}%")

# Tabla con historial
st.subheader("📋 Historial de decisiones")
st.dataframe(df.sort_values("fecha", ascending=False), use_container_width=True)

# Gráfica de acciones a lo largo del tiempo
if not df.empty:
    st.subheader("📊 Línea de tiempo de operaciones")
    chart_data = df.groupby(df['fecha'].dt.floor('h'))['accion'].value_counts().unstack().fillna(0)
    st.line_chart(chart_data)

# Gráfico de pastel: Ganancia vs Pérdida
if 'resultado' in df.columns and not df['resultado'].isnull().all():
    st.subheader("🥧 Distribución de resultados")
    resultado_counts = df['resultado'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(
        resultado_counts.values,
        labels=resultado_counts.index,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops={'edgecolor': 'white'}
    )
    ax.axis('equal')
    st.pyplot(fig)

# Refrescar automáticamente (1 vez por minuto para evitar spam a Google Sheets)
st.caption("Este panel se actualiza automáticamente cada 60 segundos.")
st_autorefresh(interval=60 * 1000, key="auto-refresh")

