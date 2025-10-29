import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, client_id="Pos3DClient", broker="broker.emqx.io", port=1883):
        self.client_id = client_id
        self.broker = broker
        self.port = port
        self.fingers_topic = "v3d/finger"
        self.position_topic = "v3d/position"
        self.client = mqtt.Client(client_id=self.client_id)
        #self.client.on_connect = self.on_connect

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Conectado al broker MQTT")
        else:
            print(f"❌ Error de conexión, código: {rc}")

    def _connect(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        self.client.on_connect = self.on_connect

    def publish_position(self, x, y, z):
        payload = f"{x} {y} {z}"  # Texto plano
        result = self.client.publish(self.position_topic, payload)
        if result[0] == 0:
            print(f"📤 Posición enviada: '{payload}'")
        else:
            print("⚠️ Error al publicar el mensaje")

    def publish_fingers(self, fingers): 
        payload = f"{fingers}"
        result = self.client.publish(self.fingers_topic, payload)
        if result[0] == 0:
            print(f"📤 Posición enviada: '{payload}'")
        else:
            print("⚠️ Error al publicar el mensaje")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
