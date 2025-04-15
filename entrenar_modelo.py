import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Cargar archivo CSV
df = pd.read_csv("btc_dataset_entrenamiento_simulado.csv")

# Separar columnas de entrada y etiqueta
X = df[['ema50', 'ema200', 'rsi', 'macd']]
y = df['label']

# Dividir entre datos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Crear y entrenar el modelo
modelo = RandomForestClassifier(n_estimators=100)
modelo.fit(X_train, y_train)

# Probarlo
predicciones = modelo.predict(X_test)
accuracy = accuracy_score(y_test, predicciones)
print(f"Precisión del modelo: {accuracy * 100:.2f}%")

# Guardar el modelo entrenado
joblib.dump(modelo, "modelo_ia.pkl")
print("Modelo guardado como modelo_ia.pkl")

