#!/usr/bin/env python3

import os
import glob
import json
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score


# -------------------------------------------------------------------------------------
# 1) Definir qué variables queremos agregar y cómo (media, máx, mín, etc.)
# -------------------------------------------------------------------------------------
AGGREGATION_FUNCTIONS = {
    # Variables típicas de conducción
    "speed": ["mean", "max"],
    "throttle": ["mean"],
    "brake": ["mean"],
    "lat_accel": ["mean", "max"],
    "long_accel": ["mean", "min"],
    # Si tienes SteeringWheelAngle, lo agregas
    "steering_angle": ["mean"],

    # Variables de setup (si existen)
    "dcBrakeBias": ["mean"],   
    "dcWingFront": ["mean"],
    "dcWingRear": ["mean"],

    # Variables ambientales (si existen por tick)
    "track_temp": ["mean"],
    "air_temp": ["mean"],

    # Ejemplo: temperatura delantera izq (si en un tick venía como LFtempCL)
    "LFtempCL": ["mean"],
    # etc. para otras
}

# -------------------------------------------------------------------------------------
# 2) Función para procesar UNA vuelta y obtener stats agregados
# -------------------------------------------------------------------------------------
def process_lap_file(filepath):
    """
    Lee lap_{n}.json, devuelve un dict con:
      {
        "lap_time_est": float,
        "speed_mean": ...,
        "speed_max": ...,
        ...
        "filename": "lap_7.json"
      }
    o None si no hay datos.
    """
    with open(filepath, "r") as f:
        lap_json = json.load(f)

    lap_data = lap_json.get("lap_data", [])
    lap_time_est = lap_json.get("lap_time_est", None)
    if not lap_data or lap_time_est is None:
        # Si no hay datos o no hay lap_time_est, descartamos esta vuelta
        return None

    # Convertir lap_data a DataFrame
    df_lap = pd.DataFrame(lap_data)

    # 1) Crear las columnas que falten en el DataFrame (forzamos a NaN)
    for col in AGGREGATION_FUNCTIONS.keys():
        if col not in df_lap.columns:
            df_lap[col] = np.nan

    # 2) Calcular las estadísticas de forma manual (en vez de .agg({col: funcs,...}))
    #    para asegurarnos de generar EXACTAMENTE las columnas definidas.
    row_dict = {}
    for col, funcs in AGGREGATION_FUNCTIONS.items():
        for func in funcs:
            col_name = f"{col}_{func}"
            # Aplica la función (mean, max, min...) si la columna es numérica
            # O si no lo es, saldrá NaN
            if func == "mean":
                val = df_lap[col].mean(skipna=True)
            elif func == "max":
                val = df_lap[col].max(skipna=True)
            elif func == "min":
                val = df_lap[col].min(skipna=True)
            # Podrías añadir más elif si usas median, std, etc.
            else:
                # Por si has metido otra función, devuelves None
                val = None
            row_dict[col_name] = val

    # 3) Añadir lap_time_est y el nombre del archivo
    row_dict["lap_time_est"] = lap_time_est
    row_dict["filename"] = os.path.basename(filepath)

    return row_dict



# -------------------------------------------------------------------------------------
# 3) Función para recorrer todos los lap_*.json y construir un DataFrame de vueltas
# -------------------------------------------------------------------------------------
def build_laps_dataset(folder="."):
    """
    Busca lap_*.json en 'folder', procesa cada uno y devuelve un DataFrame
    con una fila por vuelta y columnas de agregados + lap_time_est.
    """
    pattern = os.path.join(folder, "lap_*.json")
    files = sorted(glob.glob(pattern))

    records = []
    for file in files:
        lap_info = process_lap_file(file)
        if lap_info is not None:
            records.append(lap_info)

    df = pd.DataFrame(records)
    return df


# -------------------------------------------------------------------------------------
# 4) Script principal: construye dataset, limpia missing, entrena y evalúa
# -------------------------------------------------------------------------------------
def main():
    # 1) Construir dataset a nivel de vuelta
    df = build_laps_dataset(".")
    if df.empty:
        print("No se encontraron vueltas válidas en esta carpeta.")
        return

    print("Dataset de vueltas construido. Ejemplo de filas:\n", df.head())

    # 2) Manejo de missing data:
    #    - Si tienes muchas col. con None, decide si las rellenas con mean o drop.
    #    - Aquí, a modo de ejemplo, rellenamos con la media en todas las numéricas.
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    # 3) Definir 'lap_time_est' como target
    if "lap_time_est" not in df.columns:
        print("No existe la columna 'lap_time_est' en el dataset. Imposible entrenar modelo.")
        return

    y = df["lap_time_est"]
    # El resto de columnas numéricas (menos 'lap_time_est' y 'filename') serán features
    features = [c for c in numeric_cols if c not in ["lap_time_est"]]
    # Elimina filename si se coló en numeric_cols (generalmente es string, no numeric)
    if "filename" in features:
        features.remove("filename")

    X = df[features]

    print("\nLas features que usaremos para el modelo son:")
    print(features)

    # 4) Separar train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # 5) Entrenar un modelo simple de RandomForestRegressor
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    # 6) Predecir en test y calcular métricas
    y_pred = model.predict(X_test)
    mae = np.round(mean_absolute_error(y_test, y_pred), 3)
    r2 = np.round(r2_score(y_test, y_pred), 3)

    print(f"\nResultados del modelo RandomForest:")
    print(f"MAE = {mae}")
    print(f"R^2 = {r2}")

    # 7) Importancia de variables
    importances = model.feature_importances_
    imp_data = sorted(zip(features, importances), key=lambda x: x[1], reverse=True)
    print("\nImportancia de las features (desc):")
    for feat, val in imp_data:
        print(f"  {feat}: {val:.4f}")


if __name__ == "__main__":
    main()
