import os
import cv2
from yolo_detector import BallDetector
from mediapipe_detector import FingerCounter
from communication.mqtt_client import MQTTClient
import time
import paho.mqtt.client as mqtt

# Rutas
IMAGES_PATH_LEFT = "../data/captures/images_left"  # Carpeta con imágenes a procesar
IMAGES_PATH_RIGHT = "../data/captures/images_right"

IMG_COUNT = 0 
# Inicialización de detectores
yolo_detector = BallDetector()
finger_counter = FingerCounter()
mqtt_object = MQTTClient()
mqtt_object._connect()
try: 
    mqtt_object.client.is_connected()
except: 
    print("Ha habido un error")
print(f"Conectandose, conectado: {mqtt_object.client.is_connected()}")
while not mqtt_object.client.is_connected(): 
    print(mqtt_object.client.is_connected())
    time.sleep(1)

while f"img_{IMG_COUNT:06d}.jpg" in os.listdir(IMAGES_PATH_LEFT):
    image_left = os.path.join(IMAGES_PATH_LEFT, f"img_{IMG_COUNT:06d}.jpg")
    image_right = os.path.join(IMAGES_PATH_RIGHT, f"img_{IMG_COUNT:06d}.jpg")
    # MediaPipe conteo de dedos
    fingers, annotated_img = finger_counter.count_fingers(image_left)
    #cv2.imshow("Resultado combinado", annotated_img)
    #cv2.waitKey()
    centroide = yolo_detector.detect_stereo_ball_position(image_left, image_right)
    #print(f"Numero de dedos: {fingers}, Centroide: {centroide}")
    if fingers and centroide:
        print(fingers, centroide)
        print(f"Conectado: {mqtt_object.client.is_connected()}")
        mqtt_object.publish_position(centroide[0], centroide[1], centroide[2])
        mqtt_object.publish_fingers(fingers)
    else:
        print("🙌 No se detectaron manos o posicion")
    IMG_COUNT += 1
    # Mostrar imagen con anotaciones
    """
    cv2.imshow("Resultado combinado", annotated_img)
    key = cv2.waitKey(0) & 0xFF
    if key == ord("q"):
        break
    """

# Liberar recursos
finger_counter.close()

"""
    image = cv2.imread(image_path)

    if image is None:
        print(f"No se pudo cargar la imagen: {filename}")
        continue

    print(f"\n📸 Procesando: {filename}")

    # YOLO detección de pelota
    ball_detections = yolo_detector.detect_ball_in_cv_image(image)
    for det in ball_detections:
        print(f"🎯 Pelota detectada en: {det['centroide']} con confianza {det['confianza']}")
"""
cv2.destroyAllWindows()