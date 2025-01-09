import tkinter as tk
from tkinter import ttk
import irsdk
import time
import threading
import json
import os


# ---------------------------------------------
# CLASE TelemetryGUI (Interfaz gráfica con Tkinter)
# ---------------------------------------------
class TelemetryGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Asistente de Telemetría en Tiempo Real")
        self.master.geometry("900x700")

        # Frame principal
        self.dashboard_frame = ttk.Frame(master)
        self.dashboard_frame.pack(pady=20)

        # Etiquetas grandes de Velocidad / Marcha
        self.speed_dashboard_label = ttk.Label(self.dashboard_frame, text="Velocidad: 0 km/h", font=("Helvetica", 30))
        self.speed_dashboard_label.grid(row=0, column=0, padx=20)

        self.gear_dashboard_label = ttk.Label(self.dashboard_frame, text="Marcha: N", font=("Helvetica", 30))
        self.gear_dashboard_label.grid(row=0, column=1, padx=20)

        # Velocidad
        self.speed_label = ttk.Label(master, text="Velocidad Actual: 0 km/h", font=("Helvetica", 14))
        self.speed_label.pack(pady=5)

        # Aceleraciones
        self.lat_accel_label = ttk.Label(master, text="Aceleración Lateral: 0.00 m/s²", font=("Helvetica", 12))
        self.lat_accel_label.pack()
        self.long_accel_label = ttk.Label(master, text="Aceleración Longitudinal: 0.00 m/s²", font=("Helvetica", 12))
        self.long_accel_label.pack()

        # Ángulo de volante
        self.steering_label = ttk.Label(master, text="Ángulo del Volante: 0.00 rad", font=("Helvetica", 12))
        self.steering_label.pack()

        # Desviación en pista (puedes cambiarlo a algo más específico si quieres)
        self.position_label = ttk.Label(master, text="Desviación en Pista (ejemplo): 0.00 m", font=("Helvetica", 12))
        self.position_label.pack(pady=10)

        # Barra de progreso en la vuelta
        self.progress_label = ttk.Label(master, text="Progreso en vuelta:", font=("Helvetica", 12))
        self.progress_label.pack()
        self.progress = ttk.Progressbar(master, orient="horizontal", length=600, mode="determinate")
        self.progress.pack(pady=10)

        # Historial - cuadro de texto
        self.history_label = ttk.Label(master, text="Historial de Datos Recientes:", font=("Helvetica", 14))
        self.history_label.pack(pady=10)

        self.history_box = tk.Text(master, height=15, width=100, state="disabled", font=("Helvetica", 10))
        self.history_box.pack()

    def update_data(self, speed, gear, lat_accel, long_accel, steering_angle, position_diff, lap_progress):
        """
        Actualiza las etiquetas principales de la GUI.
        """
        # Dashboard grande
        self.speed_dashboard_label.config(text=f"Velocidad: {speed:.2f} km/h")
        self.gear_dashboard_label.config(text=f"Marcha: {gear}")

        # Detalles
        self.speed_label.config(text=f"Velocidad Actual: {speed:.2f} km/h")
        self.lat_accel_label.config(text=f"Aceleración Lateral: {lat_accel:.2f} m/s²")
        self.long_accel_label.config(text=f"Aceleración Longitudinal: {long_accel:.2f} m/s²")
        self.steering_label.config(text=f"Ángulo del Volante: {steering_angle:.2f} rad")
        self.position_label.config(text=f"Desviación en Pista (ejemplo): {position_diff:.2f} m")

        # Barra de progreso
        self.progress["value"] = lap_progress

        # Añadir una línea al historial (versión simple)
        self._add_history_line(
            f"Vel: {speed:.2f} | Marcha: {gear} | Lat: {lat_accel:.2f} | "
            f"Long: {long_accel:.2f} | Steer: {steering_angle:.2f} | PosDiff: {position_diff:.2f}\n"
        )

    def update_comparison(self, comp_info):
        """
        Muestra en la interfaz las diferencias con la vuelta de referencia.
        comp_info podría tener keys: speed_diff, brake_diff, lat_accel_diff, etc.
        """
        # Texto formateado con color según la magnitud de la diferencia
        message = "Comparación con la referencia:\n"
        message += self._colored_diff("ΔVel", comp_info["speed_diff"], unidad="km/h")
        message += self._colored_diff("ΔFreno", comp_info["brake_diff"] * 100, unidad="%")
        message += self._colored_diff("ΔThrottle", comp_info["throttle_diff"] * 100, unidad="%")
        message += self._colored_diff("ΔLatAcc", comp_info["lat_accel_diff"], unidad="m/s²")
        message += self._colored_diff("ΔLongAcc", comp_info["long_accel_diff"], unidad="m/s²")
        message += self._colored_diff("ΔSteering", comp_info["steering_diff"], unidad="rad")
        message += self._colored_diff("ΔPos", comp_info["position_diff"], unidad="%")

        self._add_history_line(message + "\n")

    # --------------------------------------------------------------------------------
    # Métodos internos para formatear texto y colorear
    # --------------------------------------------------------------------------------
    def _colored_diff(self, label, diff_value, unidad=""):
        """
        Devuelve un texto con color en base al valor de diff_value:
          - Verde si es pequeña la diferencia
          - Amarillo si es media
          - Rojo si es grande
        Ajusta los umbrales a tu gusto.
        """
        abs_val = abs(diff_value)
        if abs_val < 0.5:
            color = "green"
        elif abs_val < 2:
            color = "orange"
        else:
            color = "red"

        # Formato => label: +X.xx (unidad)
        sign = "+" if diff_value >= 0 else ""
        text_value = f"{label}: {sign}{diff_value:.2f}{unidad}  "
        return f"{self._format_color(text_value, color)}"

    def _format_color(self, text, color):
        """
        Devuelve una marca (tag) de color para usar en un Text widget de Tkinter.
        """
        return f"<<{color}>>{text}<<reset>>"

    def _add_history_line(self, text):
        """
        Inserta una línea de texto en el history_box, interpretando nuestros marcadores <<color>>.
        """
        self.history_box.config(state="normal")

        # Cortamos por '<<'
        parts = text.split("<<")
        # El primer elemento es normal text, los siguientes pueden tener color
        self.history_box.insert("end", parts[0])

        for part in parts[1:]:
            # Separa 'color>>texto<<'
            color_and_rest = part.split(">>", 1)
            if len(color_and_rest) < 2:
                # No hay marcador color
                self.history_box.insert("end", part)
                continue
            color_tag = color_and_rest[0]  # e.g. "red", "green", "reset", etc.
            rest = color_and_rest[1]

            if color_tag == "reset":
                # texto normal
                self.history_box.insert("end", rest)
            else:
                # color_tag = "red"/"green"/"orange", etc.
                if not color_tag in self.history_box.tag_names():
                    self.history_box.tag_config(color_tag, foreground=color_tag)
                # Insertamos el texto correspondiente con color
                subparts = rest.split("<<")
                self.history_box.insert("end", subparts[0], color_tag)
                if len(subparts) > 1:
                    self.history_box.insert("end", "<<".join(subparts[1:]))

        self.history_box.see("end")
        self.history_box.config(state="disabled")


# ---------------------------------------------
# CLASE TelemetryApp (Conexión con iRacing)
# ---------------------------------------------
class TelemetryApp:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.connected = False

    def connect(self):
        if not self.connected and not self.ir.is_connected:
            self.ir.startup()
            self.connected = self.ir.is_connected
            if self.connected:
                print("Conectado a iRacing.")
            else:
                print("No se pudo conectar a iRacing.")

    def disconnect(self):
        if self.connected:
            self.ir.shutdown()
            self.connected = False
            print("Desconectado de iRacing.")

    def get_telemetry_data(self):
        """
        Ajusta aquí las variables que devuelves para que coincidan con tus necesidades.
        Usamos corchetes en lugar de .get(...) porque IRSDK usa la sintaxis self.ir['Speed'], etc.
        """
        if self.connected:
            return {
                "speed": self.ir['Speed'] * 3.6,           # m/s a km/h
                "gear": self.ir['Gear'],
                "lat_accel": self.ir['LatAccel'],
                "long_accel": self.ir['LongAccel'],
                "steering_angle": self.ir['SteeringWheelAngle'],
                "LapDistPct": self.ir['LapDistPct'],    # Progreso en la vuelta (%)
                "lap": self.ir['Lap'],                    # Número de vuelta actual
                "throttle": self.ir['Throttle'],
                "brake": self.ir['Brake'],
                "session_time": self.ir['SessionTime'],
                "air_temp": self.ir['AirTemp'],           # Temperatura ambiente
                "track_temp": self.ir['TrackTemp'],       # Temperatura de la pista
                "fuel_level": self.ir['FuelLevel'],       # Nivel de combustible
                "fuel_level_pct": self.ir['FuelLevelPct'],# Porcentaje de combustible
                "dcBrakeBias": self.ir['dcBrakeBias'],    # Sesgo del freno
                "dcWingFront": self.ir['dcWingFront'],    # Ángulo del ala delantera
                "dcWingRear": self.ir['dcWingRear'],      # Ángulo del ala trasera
                "dcAntiRollFront": self.ir['dcAntiRollFront'], # Configuración del estabilizador delantero
                "dcAntiRollRear": self.ir['dcAntiRollRear'],   # Configuración del estabilizador trasero
                "LFtempL": self.ir['LFtempL'],           # Temperatura del neumático delantero izquierdo (Exterior)
                "LFtempM": self.ir['LFtempM'],           # Temperatura del neumático delantero izquierdo (Centro)
                "LFtempR": self.ir['LFtempR'],           # Temperatura del neumático delantero izquierdo (Interior)
                "RFtempL": self.ir['RFtempL'],           # Temperatura del neumático delantero derecho (Exterior)
                "RFtempM": self.ir['RFtempM'],           # Temperatura del neumático delantero derecho (Centro)
                "RFtempR": self.ir['RFtempR'],           # Temperatura del neumático delantero derecho (Interior)
                "LRtempL": self.ir['LRtempL'],           # Temperatura del neumático trasero izquierdo (Exterior)
                "LRtempM": self.ir['LRtempM'],           # Temperatura del neumático trasero izquierdo (Centro)
                "LRtempR": self.ir['LRtempR'],           # Temperatura del neumático trasero izquierdo (Interior)
                "RRtempL": self.ir['RRtempL'],           # Temperatura del neumático trasero derecho (Exterior)
                "RRtempM": self.ir['RRtempM'],           # Temperatura del neumático trasero derecho (Centro)
                "RRtempR": self.ir['RRtempR'],           # Temperatura del neumático trasero derecho (Interior)
                "LFpressure": self.ir['LFpressure'],     # Presión del neumático delantero izquierdo
                "RFpressure": self.ir['RFpressure'],     # Presión del neumático delantero derecho
                "LRpressure": self.ir['LRpressure'],     # Presión del neumático trasero izquierdo
                "RRpressure": self.ir['RRpressure']      # Presión del neumático trasero derecho
            }

        return None


# ---------------------------------------------
# CLASE LapManager (Gestión de vueltas, referencia e interpolación)
# ---------------------------------------------
class LapManager:
    def __init__(self, reference_file="best_lap.json"):
        self.reference_file = reference_file
        self.reference_lap = self.load_reference_lap(reference_file)

        # current_lap_data => datos de la vuelta actual
        self.current_lap_data = []
        self.last_lap_number = -1
        self.current_lap_start_time = 0.0
        self.best_lap_time = float('inf')

        if self.reference_lap:
            # Si el archivo tiene lap_time guardado, lo leemos
            self.best_lap_time = self._load_best_lap_time()

        # Contador para guardar vueltas individualmente
        self.lap_counter = 0

    # ---------------------------------------------
    # Carga y guarda de la vuelta de referencia
    # ---------------------------------------------
    def load_reference_lap(self, filename):
        """
        Carga el JSON de la mejor vuelta (si existe).
        Formato esperado:
        {
          "lap_time": 123.45,
          "lap_data": [
             {"LapDistPct": 0.0, "speed": 0.0, ...},
             ...
          ]
        }
        """
        if not os.path.exists(filename):
            print(f"No se encontró {filename}. Iniciando sin referencia.")
            return []

        try:
            with open(filename, 'r') as file:
                data = json.load(file)
                return data.get("lap_data", [])
        except Exception as e:
            print(f"Error cargando {filename}: {e}")
            return []

    def _load_best_lap_time(self):
        """Devuelve el tiempo de la mejor vuelta guardado en reference_file."""
        try:
            with open(self.reference_file, 'r') as file:
                data = json.load(file)
                return data.get("lap_time", float('inf'))
        except:
            return float('inf')

    def save_reference_lap(self, lap_time, lap_data):
        """
        Guarda la mejor vuelta en un JSON (reemplazando la anterior).
        """
        data = {
            "lap_time": lap_time,
            "lap_data": lap_data
        }
        with open(self.reference_file, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"¡Nueva mejor vuelta guardada! Tiempo: {lap_time:.2f}s")

    # ---------------------------------------------
    # Guardar vuelta actual completa en un archivo
    # ---------------------------------------------
    def save_current_lap_file(self, lap_data, lap_number):
        """
        Guarda la vuelta actual en un archivo JSON individual, por ejemplo "lap_3.json".
        """
        filename = f"lap_{lap_number}.json"
        # Estimación de tiempo: la primera muestra vs la última
        if lap_data:
            lap_time_est = lap_data[-1]["session_time"] - lap_data[0]["session_time"]
        else:
            lap_time_est = 0.0

        data = {
            "lap_time_est": lap_time_est,
            "lap_data": lap_data
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Vuelta {lap_number} guardada en {filename}.")

    # ---------------------------------------------
    # Lógica principal: procesar datos en cada tick
    # ---------------------------------------------
    def process_telemetry_data(self, data):
        """
        Recibe un dict con la telemetría actual y maneja:
         - Almacenar data en current_lap_data
         - Detectar si se completó una vuelta
         - Comparar con la vuelta de referencia (interpolada)
         - Devuelve un dict con las diferencias
        """
        self.current_lap_data.append(data)

        current_lap_number = data["lap"]

        # Detectar cambio de vuelta
        if current_lap_number != self.last_lap_number and self.last_lap_number != -1:
            # Ha terminado la vuelta anterior
            lap_time = data["session_time"] - self.current_lap_start_time
            self.lap_counter += 1  # Sube el contador de vueltas

            print(f"Vuelta completada (lap #{current_lap_number-1}) en {lap_time:.2f}s")
            # Guardar la vuelta completa en un JSON
            self.save_current_lap_file(self.current_lap_data, self.lap_counter)

            # ¿Es mejor que la de referencia?
            if lap_time < self.best_lap_time:
                print("¡Nueva mejor vuelta!")
                self.best_lap_time = lap_time
                self.save_reference_lap(lap_time, self.current_lap_data.copy())

            # Reseteamos para la nueva vuelta
            self.current_lap_data = []
            self.current_lap_start_time = data["session_time"]

        # Primera iteración
        if self.last_lap_number == -1:
            self.current_lap_start_time = data["session_time"]

        self.last_lap_number = current_lap_number

        # Comparar con referencia (interp)
        comp_info = self.compare_with_reference(data)

        return comp_info

    # ---------------------------------------------
    # Interpolación simple
    # ---------------------------------------------
    def interpolate_reference_point(self, current_position):
        """
        Retorna los valores de la vuelta de referencia INTERPOLADOS a LapDistPct = current_position.
        Si la referencia está vacía, None.
        """
        if not self.reference_lap:
            return None

        # Ordena la referencia por LapDistPct
        ref_data = sorted(self.reference_lap, key=lambda x: x["LapDistPct"])

        # Si current_position <= primer punto
        if current_position <= ref_data[0]["LapDistPct"]:
            return ref_data[0]

        # Si current_position >= último punto
        if current_position >= ref_data[-1]["LapDistPct"]:
            return ref_data[-1]

        # Busca dos puntos consecutivos que encierren current_position
        for i in range(len(ref_data) - 1):
            p1 = ref_data[i]
            p2 = ref_data[i+1]
            if p1["LapDistPct"] <= current_position < p2["LapDistPct"]:
                # Hacemos interpolación lineal
                ratio = ((current_position - p1["LapDistPct"]) /
                         (p2["LapDistPct"] - p1["LapDistPct"]))

                interp = {}
                for key in ["speed", "brake", "throttle", "lat_accel", "long_accel", "steering_angle"]:
                    v1 = p1.get(key, 0.0)
                    v2 = p2.get(key, 0.0)
                    interp[key] = v1 + (v2 - v1) * ratio

                # Mantén el LapDistPct interpolado
                interp["LapDistPct"] = current_position
                return interp

        # Si por algún motivo no se encontró, retorna el último
        return ref_data[-1]

    # ---------------------------------------------
    # Comparación con la vuelta de referencia
    # ---------------------------------------------
    def compare_with_reference(self, data_point):
        """
        Busca (con interpolación) el punto correspondiente en la vuelta de referencia
        y devuelve las diferencias de speed, brake, throttle, lat_accel, etc.
        """
        if not self.reference_lap:
            return {
                "speed_diff": 0.0,
                "brake_diff": 0.0,
                "throttle_diff": 0.0,
                "lat_accel_diff": 0.0,
                "long_accel_diff": 0.0,
                "steering_diff": 0.0,
                "position_diff": 0.0
            }

        current_position = data_point["LapDistPct"]
        ref_point = self.interpolate_reference_point(current_position)
        if ref_point is None:
            # No hay datos de referencia
            return {
                "speed_diff": 0.0,
                "brake_diff": 0.0,
                "throttle_diff": 0.0,
                "lat_accel_diff": 0.0,
                "long_accel_diff": 0.0,
                "steering_diff": 0.0,
                "position_diff": 0.0
            }

        # Calculamos diffs
        speed_diff = data_point["speed"] - ref_point["speed"]
        brake_diff = data_point["brake"] - ref_point["brake"]
        throttle_diff = data_point["throttle"] - ref_point["throttle"]
        lat_accel_diff = data_point["lat_accel"] - ref_point["lat_accel"]
        long_accel_diff = data_point["long_accel"] - ref_point["long_accel"]
        steering_diff = data_point["steering_angle"] - ref_point["steering_angle"]
        # Por ejemplo, en % de diferencia de posición en el circuito
        position_diff = (current_position - ref_point["LapDistPct"]) * 100

        return {
            "speed_diff": speed_diff,
            "brake_diff": brake_diff,
            "throttle_diff": throttle_diff,
            "lat_accel_diff": lat_accel_diff,
            "long_accel_diff": long_accel_diff,
            "steering_diff": steering_diff,
            "position_diff": position_diff
        }


# ---------------------------------------------
# FUNCIÓN que corre en un hilo para actualizar la GUI y la lógica de vueltas
# ---------------------------------------------
def update_gui(gui, app, lap_manager):
    """
    Hilo que corre en paralelo al mainloop de Tkinter.
    Cada ~50 ms:
      1) Conectar a iRacing si no está conectado
      2) Obtener datos telemetría
      3) Pasarlo a LapManager para procesar
      4) Actualizar GUI con data y comparación
    """
    while True:
        app.connect()
        if app.connected:
            data = app.get_telemetry_data()
            if data:
                # Procesar en LapManager (almacena, detecta vuelta, compara)
                comparison_info = lap_manager.process_telemetry_data(data)

                # Actualizar GUI principal
                gui.update_data(
                    speed=data["speed"],
                    gear=data["gear"],
                    lat_accel=data["lat_accel"],
                    long_accel=data["long_accel"],
                    steering_angle=data["steering_angle"],
                    position_diff=comparison_info["position_diff"],
                    lap_progress=data["LapDistPct"] * 100
                )

                # Mostrar deltas
                gui.update_comparison(comparison_info)

        time.sleep(0.05)  # ~ 20 Hz


# ---------------------------------------------
# MAIN
# ---------------------------------------------
if __name__ == "__main__":
    # 1) Iniciar ventana
    root = tk.Tk()
    gui = TelemetryGUI(root)

    # 2) Iniciar clase que se conecta a iRacing
    app = TelemetryApp()

    # 3) LapManager para gestionar vueltas y referencia
    lap_manager = LapManager("best_lap.json")

    # 4) Hilo de actualización
    threading.Thread(
        target=update_gui,
        args=(gui, app, lap_manager),
        daemon=True
    ).start()

    # 5) Arrancar el bucle principal de Tkinter
    root.mainloop()
