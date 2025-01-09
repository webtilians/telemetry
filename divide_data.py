#!/usr/bin/env python3
import os
import glob
import json
import numpy as np
import pandas as pd

# Definimos sectores para Tsukuba, ejemplo ficticio (ajusta porcentajes reales)
SECTORS = {
    "sector1": (0.00, 0.33),  # LapDistPct de 0% a 33%
    "sector2": (0.33, 0.66),  # 33% a 66%
    "sector3": (0.66, 1.00)   # 66% a 100%
}

def process_lap_file(filepath):
    """
    Lee lap_{n}.json y devuelve un dict con:
      - lap_time_est
      - fuel_level_init
      - stats por cada sector: speed_min, speed_max, brake_max, etc.
      - Ignora ticks con OnPitRoad==True o IsInGarage==True
    """
    with open(filepath, "r") as f:
        lap_json = json.load(f)

    lap_data = lap_json.get("lap_data", [])
    lap_time_est = lap_json.get("lap_time_est", None)
    if not lap_data or lap_time_est is None:
        return None

    df_lap = pd.DataFrame(lap_data)

    # A) Eliminar ticks en pit o garage
    if "OnPitRoad" in df_lap.columns:
        df_lap = df_lap[df_lap["OnPitRoad"] == False]
    if "IsInGarage" in df_lap.columns:
        df_lap = df_lap[df_lap["IsInGarage"] == False]

    # B) Asegurar que lap_dist_pct y fuel_level existen (si no, creamos NaN)
    if "lap_dist_pct" not in df_lap.columns:
        df_lap["lap_dist_pct"] = np.nan
    if "FuelLevel" not in df_lap.columns:
        df_lap["FuelLevel"] = np.nan

    # C) Tomar "fuel_level_init" como el FuelLevel al inicio de la vuelta (primer tick)
    if not df_lap.empty:
        fuel_level_init = df_lap["FuelLevel"].iloc[0]
    else:
        fuel_level_init = np.nan

    # D) Sectorizar
    row_dict = {}
    for sector_name, (start_pct, end_pct) in SECTORS.items():
        df_sec = df_lap[
            (df_lap["lap_dist_pct"] >= start_pct) &
            (df_lap["lap_dist_pct"] < end_pct)
        ]
        if df_sec.empty:
            # Si no hay datos en ese sector, rellenamos con NaN
            row_dict[f"{sector_name}_speed_min"] = np.nan
            row_dict[f"{sector_name}_speed_max"] = np.nan
            row_dict[f"{sector_name}_brake_max"] = np.nan
        else:
            # Ejemplo de stats: velocidad min, max, brake max
            row_dict[f"{sector_name}_speed_min"] = df_sec["speed"].min(skipna=True) if "speed" in df_sec.columns else np.nan
            row_dict[f"{sector_name}_speed_max"] = df_sec["speed"].max(skipna=True) if "speed" in df_sec.columns else np.nan
            row_dict[f"{sector_name}_brake_max"] = df_sec["brake"].max(skipna=True) if "brake" in df_sec.columns else np.nan

    # E) Guardar lap_time_est y fuel_level_init
    row_dict["lap_time_est"] = lap_time_est
    row_dict["fuel_level_init"] = fuel_level_init
    row_dict["filename"] = os.path.basename(filepath)

    return row_dict

def build_laps_dataset(folder="."):
    """
    Recorre lap_*.json, sectoriza cada vuelta y retorna un DataFrame con una fila por vuelta.
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

def main():
    df = build_laps_dataset(".")
    if df.empty:
        print("No se han encontrado vueltas válidas.")
        return

    print("Dataset de sectores:")
    print(df.head())

    # Limpieza rápida de NaN
    # Ej. si hay muchas sector_n_speed_min en NaN, se puede imputar o dejar
    df = df.fillna(df.mean(numeric_only=True))

    # Un mini ejemplo de entrenamiento
    # Tomamos lap_time_est como target, features: fuel_level_init y sector speeds
    features = [c for c in df.columns if c not in ("lap_time_est", "filename")]
    # Si hay columns que no sirven, las sacas
    X = df[features]
    y = df["lap_time_est"]

    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\nEntrenamiento random forest con sectorización:")
    print(f"MAE = {mae:.3f}")
    print(f"R^2 = {r2:.3f}")

    # Importancias
    importances = model.feature_importances_
    sorted_imp = sorted(zip(features, importances), key=lambda x: x[1], reverse=True)
    print("\nImportancia de features (desc):")
    for f, val in sorted_imp:
        print(f"{f}: {val:.4f}")

if __name__ == "__main__":
    main()
