import tkinter as tk
from tkinter import ttk
import irsdk
import time
import threading


class TelemetryGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Asistente de Telemetría en Tiempo Real")
        self.master.geometry("800x600")

        # Dashboard grande para velocidad y marcha
        self.dashboard_frame = ttk.Frame(master)
        self.dashboard_frame.pack(pady=20)

        self.speed_dashboard_label = ttk.Label(self.dashboard_frame, text="Velocidad: 0 km/h", font=("Helvetica", 30))
        self.speed_dashboard_label.grid(row=0, column=0, padx=20)

        self.gear_dashboard_label = ttk.Label(self.dashboard_frame, text="Marcha: N", font=("Helvetica", 30))
        self.gear_dashboard_label.grid(row=0, column=1, padx=20)

        # Velocidad
        self.speed_label = ttk.Label(master, text="Velocidad Actual: 0 km/h", font=("Helvetica", 14))
        self.speed_label.pack(pady=10)

        # Aceleración lateral y longitudinal
        self.lat_accel_label = ttk.Label(master, text="Aceleración Lateral: 0.00 m/s²", font=("Helvetica", 12))
        self.lat_accel_label.pack()
        self.long_accel_label = ttk.Label(master, text="Aceleración Longitudinal: 0.00 m/s²", font=("Helvetica", 12))
        self.long_accel_label.pack()

        # Ángulo del volante
        self.steering_label = ttk.Label(master, text="Ángulo del Volante: 0.00 rad", font=("Helvetica", 12))
        self.steering_label.pack()

        # Diferencia de posición
        self.position_label = ttk.Label(master, text="Desviación en Pista: 0.00 m", font=("Helvetica", 12))
        self.position_label.pack(pady=10)

        # Barra de progreso (posición en pista)
        self.progress_label = ttk.Label(master, text="Progreso en pista:", font=("Helvetica", 12))
        self.progress_label.pack()
        self.progress = ttk.Progressbar(master, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=20)

        # Historial de datos recientes
        self.history_label = ttk.Label(master, text="Historial de Datos Recientes:", font=("Helvetica", 14))
        self.history_label.pack(pady=10)

        self.history_box = tk.Text(master, height=10, width=80, state="disabled", font=("Helvetica", 10))
        self.history_box.pack()

        # Resumen de vuelta
        self.lap_summary_label = ttk.Label(master, text="Resumen de Vuelta:", font=("Helvetica", 14))
        self.lap_summary_label.pack(pady=10)
        self.lap_summary_text = ttk.Label(master, text="Tiempo de vuelta: N/A\nDesviación promedio: N/A", font=("Helvetica", 12))
        self.lap_summary_text.pack()

    def update_data(self, speed, gear, lat_accel, long_accel, steering_angle, position_diff, lap_progress):
        """Actualiza los datos mostrados en la interfaz."""
        # Actualización del dashboard grande
        self.speed_dashboard_label.config(text=f"Velocidad: {speed:.2f} km/h")
        self.gear_dashboard_label.config(text=f"Marcha: {gear}")

        # Actualización de etiquetas
        self.speed_label.config(text=f"Velocidad Actual: {speed:.2f} km/h")
        self.lat_accel_label.config(text=f"Aceleración Lateral: {lat_accel:.2f} m/s²")
        self.long_accel_label.config(text=f"Aceleración Longitudinal: {long_accel:.2f} m/s²")
        self.steering_label.config(text=f"Ángulo del Volante: {steering_angle:.2f} rad")
        self.position_label.config(text=f"Desviación en Pista: {position_diff:.2f} m")
        self.progress["value"] = lap_progress  # Actualiza la barra de progreso

        # Historial de datos recientes
        self.history_box.config(state="normal")
        self.history_box.insert(
            "end",
            f"Velocidad: {speed:.2f} km/h | Marcha: {gear} | Lat: {lat_accel:.2f} m/s² | Long: {long_accel:.2f} m/s² | Posición: {position_diff:.2f} m\n"
        )
        self.history_box.see("end")
        self.history_box.config(state="disabled")

    def update_lap_summary(self, lap_time, avg_deviation):
        """Actualiza el resumen de vuelta."""
        self.lap_summary_text.config(
            text=f"Tiempo de vuelta: {lap_time:.2f} s\nDesviación promedio: {avg_deviation:.2f} m"
        )


class TelemetryApp:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.connected = False
        self.current_lap_data = []

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
        if self.connected:
            return {
                "speed": self.ir['Speed'] * 3.6,
                "gear": self.ir['Gear'],
                "lat_accel": self.ir['LatAccel'],
                "long_accel": self.ir['LongAccel'],
                "steering_angle": self.ir['SteeringWheelAngle'],
                "LapDistPct": self.ir['LapDistPct']
            }
        return None


def update_gui(gui, app):
    """Ciclo de actualización de la GUI."""
    while True:
        app.connect()
        if app.connected:
            data = app.get_telemetry_data()
            if data:
                gui.update_data(
                    speed=data["speed"],
                    gear=data["gear"],
                    lat_accel=data["lat_accel"],
                    long_accel=data["long_accel"],
                    steering_angle=data["steering_angle"],
                    position_diff=0.0,  # Placeholder para futuras mejoras
                    lap_progress=data["LapDistPct"] * 100
                )
        time.sleep(0.05)  # Actualización cada 50 ms


if __name__ == "__main__":
    root = tk.Tk()
    gui = TelemetryGUI(root)
    app = TelemetryApp()

    # Iniciar la actualización en un hilo separado
    threading.Thread(target=update_gui, args=(gui, app), daemon=True).start()

    root.mainloop()
