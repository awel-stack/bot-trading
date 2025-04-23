import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from streamlit_autorefresh import st_autorefresh
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="📊 Dashboard del Bot", layout="wide")
st.title("🤖 Dashboard del Bot de Trading")

# Autorefresh cada minuto
st_autorefresh(interval=60000, key="data_refresh")

# Conexión a PostgreSQL desde secrets.toml
DATABASE_URL = st.secrets["POSTGRES_URL"]

try:
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    st.write("✅ Conexión establecida con PostgreSQL")  # Temporal, para confirmar
except Exception as e:
    st.error(f"❌ Error de conexión a la base de datos: {e}")
    st.stop()

# Cargar datos
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_sql("SELECT * FROM decisiones ORDER BY fecha DESC", conn)
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")
        return pd.DataFrame()

df = cargar_datos()

# Métricas
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total decisiones", len(df))
col2.metric("BUY", (df['accion'] == 'buy').sum())
col3.metric("SELL", (df['accion'] == 'sell').sum())
col4.metric("HOLD", (df['accion'] == 'hold').sum())
if 'resultado' in df.columns:
    aciertos = (df['resultado'] == 'ganancia').sum()
    total_validas = df['resultado'].isin(['ganancia', 'pérdida']).sum()
    efectividad = (aciertos / total_validas) * 100 if total_validas > 0 else 0
    col5.metric("🎯 Efectividad", f"{efectividad:.1f}%")

# Tabla
st.subheader("📋 Historial de decisiones")
st.dataframe(df, use_container_width=True)

# Línea de tiempo
if not df.empty:
    st.subheader("📈 Línea de tiempo de decisiones")
    df_chart = df.groupby(df['fecha'].dt.floor('h'))['accion'].value_counts().unstack().fillna(0)
    st.line_chart(df_chart)

# Gráfico de pastel
if 'resultado' in df.columns:
    st.subheader("🥧 Distribución de resultados")
    resultado_counts = df['resultado'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(resultado_counts.values, labels=resultado_counts.index, autopct='%1.1f%%', startangle=90)
    ax.axis("equal")
    st.pyplot(fig)

# Cierre
conn.close()