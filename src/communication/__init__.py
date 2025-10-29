"""
from mqtt_client import MQTTClient
import time

def main():
    mqtt = MQTTClient(broker="broker.emqx.io", port=1883, topic="v3d/position")
    mqtt.connect()

    time.sleep(1)  # Esperamos un poco para asegurar la conexión

    # Ejemplo de publicación
    mqtt.publish_position(100.0, 20.5, -0.80)

    time.sleep(1)
    mqtt.disconnect()

if __name__ == "__main__":
    main()
"""