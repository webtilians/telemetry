import irsdk
import json
import time


class LapManager:
    def __init__(self, reference_file="best_lap.json"):
        self.ir = irsdk.IRSDK()
        self.connected = False
        self.reference_lap = self.load_reference_lap(reference_file)  # Datos de la mejor vuelta
        self.current_lap_data = []  # Datos de la vuelta actual
        self.last_lap_pct = 0  # Porcentaje de distancia en la última iteración
        self.current_lap_start_time = 0  # Tiempo de inicio de la vuelta actual
        self.best_lap_time = float('inf')  # Tiempo de la mejor vuelta (inicialmente infinito)
        self.last_lap_number = -1  # Número de la última vuelta
        self.reference_file = reference_file
        self.current_lap_file = "current_lap.json"  # Archivo para la vuelta actual

    def connect(self):
        """Conecta a iRacing."""
        if not self.connected and not self.ir.is_connected:
            self.ir.startup()
            self.connected = self.ir.is_connected
            if self.connected:
                print("Conectado a iRacing.")
            else:
                print("No se pudo conectar a iRacing. Asegúrate de que esté ejecutándose.")

    def disconnect(self):
        """Desconecta de iRacing."""
        if self.connected:
            self.ir.shutdown()
            self.connected = False
            print("Desconectado de iRacing.")

    def load_reference_lap(self, filename):
        """Carga los datos de la mejor vuelta desde un archivo JSON."""
        try:
            with open(filename, 'r') as file:
                print(f"Cargando mejor vuelta desde {filename}...")
                data = json.load(file)
                self.best_lap_time = data.get("lap_time", float('inf'))
                return data.get("lap_data", [])
        except FileNotFoundError:
            print(f"No se encontró el archivo de referencia {filename}. Creando uno nuevo.")
            return []

    def save_current_lap(self):
        """Guarda los datos de la vuelta actual en un archivo JSON."""
        if self.current_lap_data:
            with open(self.current_lap_file, 'w') as file:
                json.dump(self.current_lap_data, file, indent=4)
            print(f"Datos de la vuelta actual guardados en {self.current_lap_file}.")
        else:
            print("No hay datos de vuelta actual para guardar.")

    def save_reference_lap(self, lap_time, lap_data):
        """Guarda la mejor vuelta en un archivo JSON."""
        data = {"lap_time": lap_time, "lap_data": lap_data}
        with open(self.reference_file, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Mejor vuelta guardada en {self.reference_file} con tiempo: {lap_time:.2f}s")

    def compare_with_reference(self, data_point):
        """Compara los datos actuales con la mejor vuelta."""
        if not self.reference_lap:
            print("No hay vuelta de referencia para comparar.")
            return

        current_position = data_point["LapDistPct"]
        closest_point = min(
            self.reference_lap,
            key=lambda ref: abs(ref["LapDistPct"] - current_position)
        )

        # Comparar velocidad
        speed_diff = data_point["Speed"] - closest_point["Speed"]
        if abs(speed_diff) > 1:  # Mostrar si la diferencia es significativa
            print(f"Velocidad: Actual {data_point['Speed']:.2f} km/h | Referencia {closest_point['Speed']:.2f} km/h | Diferencia {speed_diff:.2f} km/h")

        # Comparar acelerador
        throttle_diff = data_point["Throttle"] - closest_point["Throttle"]
        if abs(throttle_diff) > 0.1:  # Mostrar si la diferencia es significativa
            print(f"Acelerador: Actual {data_point['Throttle']*100:.1f}% | Referencia {closest_point['Throttle']*100:.1f}% | Diferencia {throttle_diff*100:.1f}%")

        # Comparar freno
        brake_diff = data_point["Brake"] - closest_point["Brake"]
        if abs(brake_diff) > 0.1:  # Mostrar si la diferencia es significativa
            print(f"Freno: Actual {data_point['Brake']*100:.1f}% | Referencia {closest_point['Brake']*100:.1f}% | Diferencia {brake_diff*100:.1f}%")

        # Comparar posición en pista
        lap_dist_diff = data_point["LapDistPct"] - closest_point["LapDistPct"]
        print(f"Posición en pista: Actual {data_point['LapDistPct']:.2f} | Referencia {closest_point['LapDistPct']:.2f} | Diferencia {lap_dist_diff:.2f}")

        # Comparar aceleración lateral y longitudinal
        lat_accel_diff = data_point["LatAccel"] - closest_point["LatAccel"]
        long_accel_diff = data_point["LongAccel"] - closest_point["LongAccel"]
        print(f"Aceleración lateral: Actual {data_point['LatAccel']:.2f} m/s² | Referencia {closest_point['LatAccel']:.2f} m/s² | Diferencia {lat_accel_diff:.2f} m/s²")
        print(f"Aceleración longitudinal: Actual {data_point['LongAccel']:.2f} m/s² | Referencia {closest_point['LongAccel']:.2f} m/s² | Diferencia {long_accel_diff:.2f} m/s²")

        # Comparar ángulo del volante
        steering_diff = data_point["SteeringWheelAngle"] - closest_point["SteeringWheelAngle"]
        print(f"Ángulo del volante: Actual {data_point['SteeringWheelAngle']:.2f} rad | Referencia {closest_point['SteeringWheelAngle']:.2f} rad | Diferencia {steering_diff:.2f} rad")

    def analyze_telemetry(self):
        """Analiza los datos de telemetría en tiempo real."""
        if self.ir.is_connected:
            data_point = {
                "Lap": self.ir['Lap'],  # Número de vuelta actual
                "LapDistPct": self.ir['LapDistPct'],  # Porcentaje completado de la vuelta
                "Speed": self.ir['Speed'] * 3.6,  # Velocidad en km/h
                "Throttle": self.ir['Throttle'],  # Acelerador
                "Brake": self.ir['Brake'],  # Frenado
                "SessionTime": self.ir['SessionTime'],  # Tiempo total de la sesión
                "LapCurrentLapTime": self.ir['LapCurrentLapTime'],  # Tiempo actual de la vuelta
                "LatAccel": self.ir['LatAccel'],  # Aceleración lateral
                "LongAccel": self.ir['LongAccel'],  # Aceleración longitudinal
                "SteeringWheelAngle": self.ir['SteeringWheelAngle']  # Ángulo del volante
            }

            self.current_lap_data.append(data_point)
            self.save_current_lap()  # Guardar continuamente la vuelta actual

            # Detectar cambio de vuelta usando `Lap`
            if data_point["Lap"] != self.last_lap_number:
                lap_time = data_point["SessionTime"] - self.current_lap_start_time
                print(f"Vuelta completada: Tiempo {lap_time:.2f}s")

                # Guardar datos de la vuelta actual en `current_lap.json`
                self.save_current_lap()

                # Reiniciar para la nueva vuelta
                self.current_lap_data = []
                self.current_lap_start_time = data_point["SessionTime"]

            # Comparar con la vuelta de referencia
            self.compare_with_reference(data_point)

            # Actualizar últimos valores
            self.last_lap_number = data_point["Lap"]

    def run(self):
        """Ejecuta el manejador de vueltas en tiempo real."""
        print("Iniciando el asistente en tiempo real...")
        try:
            while True:
                if not self.connected:
                    self.connect()
                if self.connected:
                    self.analyze_telemetry()
                time.sleep(1 / 60)  # Frecuencia de actualización
        except KeyboardInterrupt:
            print("\nAsistente detenido.")
            print("Guardando la vuelta actual antes de salir...")
            self.save_current_lap()  # Guardar los datos al detener el programa
        finally:
            self.disconnect()


if __name__ == "__main__":
    manager = LapManager()
    manager.run()
