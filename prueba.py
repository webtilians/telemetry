import irsdk
import time

# Conexión con iRacing
class IRacingParameterTester:
    def __init__(self):
        self.ir = irsdk.IRSDK()  # Inicialización correcta de IRSDK
        self.connected = False

    def connect(self):
        if not self.connected and not self.ir.is_connected:
            self.ir.startup()
            self.connected = self.ir.is_connected
            if self.connected:
                print("Conectado a iRacing.")
            else:
                print("No se pudo conectar a iRacing. Asegúrate de que esté ejecutándose.")

    def disconnect(self):
        if self.connected:
            self.ir.shutdown()
            self.connected = False
            print("Desconectado de iRacing.")

    def test_parameters(self):
        if not self.connected:
            print("No estás conectado a iRacing. Conéctate primero.")
            return

        # Lista completa de parámetros basada en el PDF
        parameters = [
            "AirDensity", "AirPressure", "AirTemp", "Alt", "Brake", "BrakeRaw", "CamCameraNumber",
            "CamCameraState", "CamCarIdx", "CamGroupNumber", "Clutch", "CpuUsageBG", "DCDriversSoFar",
            "DCLapStatus", "DisplayUnits", "DriverMarker", "EngineWarnings", "EnterExitReset", "FogLevel",
            "FrameRate", "FuelLevel", "FuelLevelPct", "FuelPress", "FuelUsePerHour", "Gear", "IsDiskLoggingActive",
            "IsDiskLoggingEnabled", "IsInGarage", "IsOnTrack", "IsOnTrackCar", "IsReplayPlaying", "Lap",
            "LapBestLap", "LapBestLapTime", "LapBestNLapLap", "LapBestNLapTime", "LapCurrentLapTime",
            "LapDeltaToBestLap", "LapDeltaToBestLap_DD", "LapDeltaToBestLap_OK", "LapDeltaToOptimalLap",
            "LapDeltaToOptimalLap_DD", "LapDeltaToOptimalLap_OK", "LapDeltaToSessionBestLap",
            "LapDeltaToSessionBestLap_DD", "LapDeltaToSessionBestLap_OK", "LapDeltaToSessionLastlLap",
            "LapDeltaToSessionLastlLap_DD", "LapDeltaToSessionLastlLap_OK", "LapDeltaToSessionOptimalLap",
            "LapDeltaToSessionOptimalLap_DD", "LapDeltaToSessionOptimalLap_OK", "LapDist", "LapDistPct",
            "LapLasNLapSeq", "LapLastLapTime", "LapLastNLapTime", "Lat", "LatAccel", "Lon", "LongAccel",
            "ManifoldPress", "OilLevel", "OilPress", "OilTemp", "OnPitRoad", "Pitch", "PitchRate",
            "PitOptRepairLeft", "PitRepairLeft", "PitSvFlags", "PitSvFuel", "PitSvLFP", "PitSvLRP", "PitSvRFP",
            "PitSvRRP", "PlayerCarClassPosition", "PlayerCarPosition", "RaceLaps", "RadioTransmitCarIdx",
            "RadioTransmitFrequencyIdx", "RadioTransmitRadioIdx", "RelativeHumidity", "ReplayFrameNum",
            "ReplayFrameNumEnd", "ReplayPlaySlowMotion", "ReplayPlaySpeed", "ReplaySessionNum",
            "ReplaySessionTime", "Roll", "RollRate", "RPM", "SessionFlags", "SessionLapsRemain", "SessionNum",
            "SessionState", "SessionTime", "SessionTimeRemain", "SessionUniqueID", "ShiftGrindRPM",
            "ShiftIndicatorPct", "ShiftPowerPct", "Skies", "Speed", "SteeringWheelAngle",
            "SteeringWheelAngleMax", "SteeringWheelPctDamper", "SteeringWheelPctTorque",
            "SteeringWheelPctTorqueSign", "SteeringWheelPctTorqueSignStops", "SteeringWheelPeakForceNm",
            "SteeringWheelTorque", "Throttle", "ThrottleRaw", "TrackTemp", "TrackTempCrew", "VelocityX",
            "VelocityY", "VelocityZ", "VertAccel", "Voltage", "WaterLevel", "WaterTemp", "WeatherType",
            "WindDir", "WindVel", "Yaw", "YawNorth", "YawRate"
        ]

        # Iterar sobre los parámetros y comprobar su disponibilidad
        print("\n--- Resultados de los parámetros ---")
        for param in parameters:
            try:
                # Intentar acceder directamente al parámetro
                value = self.ir[param]  # Acceso directo a la variable
                print(f"{param}: {value}")
            except KeyError:
                print(f"{param}: No disponible (KeyError)")
            except Exception as e:
                print(f"{param}: Error inesperado: {e}")

# Main
if __name__ == "__main__":
    tester = IRacingParameterTester()

    try:
        tester.connect()
        if tester.connected:
            print("Esperando 5 segundos para que iRacing inicie datos...")
            time.sleep(5)  # Tiempo para que iRacing comience a transmitir datos
            tester.test_parameters()
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
    finally:
        tester.disconnect()
