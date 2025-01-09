#!/usr/bin/env python3

import os
import glob
import json
import pandas as pd

# Variables esenciales (conducción + condiciones) que esperamos encontrar en cada muestra
ESSENTIAL_VARS = [
    "session_time",
    "lap",
    "lap_dist_pct",
    "speed",
    "throttle",
    "brake",
    "lat_accel",
    "long_accel",
    "steering_angle",
    "air_temp",
    "track_temp",
    "fuel_level",
    "fuel_level_pct"
]

# Variables de asesoramiento de setup que queramos incluir
# (ojo, solo algunos coches reportan dcBrakeBias, dcWingFront, etc.)
SETUP_VARS = [
    "dcBrakeBias",
    "dcWingFront",
    "dcWingRear",
    "dcAntiRollFront",
    "dcAntiRollRear",
    "LFtempL", "LFtempM", "LFtempR",
    "RFtempL", "RFtempM", "RFtempR",
    "LRtempL", "LRtempM", "LRtempR",
    "RRtempL", "RRtempM", "RRtempR",
    "LFpressure", "RFpressure","LRpressure", "RRpressure",
    # Añade más si lo deseas, p. ej. "dcTractionControl", etc.
]

# Unimos ambas listas para procesarlas juntas
ALL_VARS = ESSENTIAL_VARS + SETUP_VARS

def prepare_dataset(laps_dir="."):
    """
    Recorre los archivos 'lap_*.json' en 'laps_dir' para generar un DataFrame
    con las columnas de ALL_VARS + lap_time_est (sacado del JSON).
    Retorna el DataFrame final.
    """
    records = []

    # Buscar todos los archivos con nombre lap_*.json
    pattern = os.path.join(laps_dir, "lap_*.json")
    files = sorted(glob.glob(pattern))

    for file in files:
        with open(file, "r") as f:
            lap_data_json = json.load(f)

        # Extraer lap_time_est (si quieres usarlo como target de un modelo)
        lap_time_est = lap_data_json.get("lap_time_est", None)

        # Recorrer las muestras de "lap_data"
        lap_samples = lap_data_json.get("lap_data", [])
        for sample in lap_samples:
            # Construir un dict con las columnas que nos interesan
            row = {}

            # Ej. row["lap_time_est"] = lap_time_est para saber a qué vuelta corresponde
            # Podrías querer etiquetar cada fila con el tiempo total de esa vuelta
            row["lap_time_est"] = lap_time_est

            # Rellenar las variables en ALL_VARS (o poner None si no existen)
            for var in ALL_VARS:
                if var in sample:
                    row[var] = sample[var]
                else:
                    # Caso en que no exista en el sample
                    row[var] = None

            # También podrías añadir la info del nombre de archivo si quieres
            # row["file_source"] = os.path.basename(file)

            records.append(row)

    # Convertir todo a DataFrame
    df = pd.DataFrame(records)

    # Ordenar columnas: que "lap_time_est" salga cerca del final, etc.
    # (opcional) 
    cols_order = ["lap_time_est"] + ALL_VARS
    df = df[cols_order]

    return df


if __name__ == "__main__":
    # 1) Cargar datos
    df = prepare_dataset(".")
    # 2) Echar un vistazo
    print("Primera filas del DataFrame:")
    print(df.head())
    # 3) Guardar en un CSV para entrenar el modelo
    output_csv = "telemetry_dataset.csv"
    df.to_csv(output_csv, index=False)
    print(f"\nDataset guardado en '{output_csv}' con {len(df)} filas.")
