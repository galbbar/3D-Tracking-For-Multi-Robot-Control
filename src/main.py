import os
import cv2
import pyzed.sl as sl
import time
from yolo_detector import BallDetector
from mediapipe_detector import FingerCounter
from communication.mqtt_client import MQTTClient
import paho.mqtt.client as mqtt
import threading 

class ZEDCamera():
    """
    Cámara ZED2 para capturar imágenes y guardarlas en un directorio.
    """

    def __init__(self, camera_name, fps, left_path, right_path):
        self.name = 'camera_' + camera_name
        self.fps = fps
        self.left_path = left_path
        self.right_path = right_path
        self.img_count = 0

        self.yolo_detector = BallDetector()
        self.finger_counter = FingerCounter()
        self.mqtt_object = MQTTClient()
        self.mqtt_object._connect()
        while not self.mqtt_object.client.is_connected(): 
            print(self.mqtt_object.client.is_connected())
            time.sleep(1)

        # Crea el directorio si no existe
        #if not os.path.exists(self.path):
        #    os.makedirs(self.path)

        # Inicializa la cámara ZED
        self.cam = sl.Camera()
        init_params = sl.InitParameters()
        init_params.camera_resolution = sl.RESOLUTION.HD1080  # Resolución HD1080
        init_params.depth_mode = sl.DEPTH_MODE.ULTRA  # Modo de profundidad
        init_params.coordinate_units = sl.UNIT.METER
        init_params.camera_fps = self.fps
        status = self.cam.open(init_params)
        if status != sl.ERROR_CODE.SUCCESS:
            print("Error al abrir la cámara ZED2")
            exit(1)

    def capture_images(self):
        runtime = sl.RuntimeParameters()
        mat = sl.Mat()

        key = -1  # Inicializamos la tecla para evitar que entre en el loop

        while key != 113:  # 'q' para salir
            err = self.cam.grab(runtime)
            if err == sl.ERROR_CODE.SUCCESS:
                # Captura la imagen de la cámara ZED2
                for orientation in ["l", "r"]:
                    if orientation == "l": 
                        self.cam.retrieve_image(mat, sl.VIEW.LEFT)
                        filename = os.path.join(self.left_path, f"img_{self.img_count:06d}.jpg")
                    else: 
                        self.cam.retrieve_image(mat, sl.VIEW.RIGHT)
                        filename = os.path.join(self.right_path, f"img_{self.img_count:06d}.jpg")
                    cvImage = mat.get_data()  # Convierte a formato compatible con OpenCV

                    cv2.imwrite(filename, cvImage)
                    print(f"Imagen guardada como {filename}")
                self.img_count += 1
                time.sleep(1)



                # Muestra la imagen en una ventana
                cv2.imshow("ZED Camera - Live Feed", cvImage)
                key = cv2.waitKey(1)  # Espera por 1 ms para una tecla
            else:
                print(f"Error al capturar la imagen: {err}")
                break

        # Libera los recursos
        self.cam.close()
        cv2.destroyAllWindows()

    def process(self): 
        IMG_COUNT = 0 
        while True: 
            #time.sleep(1)
            left_image_name = f"img_{IMG_COUNT:06d}.jpg"
            right_image_name = f"img_{IMG_COUNT:06d}.jpg"

            left_image_path = os.path.join(self.left_path, left_image_name)
            right_image_path = os.path.join(self.right_path, right_image_name)
            if os.path.exists(left_image_path) and os.path.exists(right_image_path):
                # Procesar ambas imágenes si existen
                fingers, annotated_img = self.finger_counter.count_fingers(left_image_path)
                ruta_completa = os.path.join("pelota", f"img_{IMG_COUNT:06d}.jpg")
                #cv2.imwrite(ruta_completa, annotated_img)
                #print(f"Guardando imagen en {ruta_completa}")
                centroide = self.yolo_detector.detect_stereo_ball_position(left_image_path, right_image_path)
                print(fingers, centroide)
                if fingers and centroide:
                    print(f"📡 Publicando -> Dedos: {fingers}, Centroide: {centroide}")
                    self.mqtt_object.publish_position(*centroide)
                    self.mqtt_object.publish_fingers(fingers)
                else:
                    print("🙌 No se detectaron manos o posición")

                IMG_COUNT += 1

# Crear una instancia de la clase ZEDCamera
if __name__ == "__main__":
    # Nombre de la cámara, FPS y carpeta de guardado
    camera_name = "ZED2"
    fps = 0.01  # FPS de la cámara
    save_left_path = "../data/captures/images_left"  # Directorio para guardar las imágenes
    save_right_path = "../data/captures/images_right"
    for dir in [save_left_path, save_right_path]: 
        for filename in os.listdir(dir):
            file_path = os.path.join(dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)


    # Crear objeto de cámara ZED
    zed_camera = ZEDCamera(camera_name, fps, save_left_path, save_right_path)


    hilo1 = threading.Thread(target=zed_camera.capture_images, daemon = True)
    hilo2 = threading.Thread(target=zed_camera.process, daemon = True)

    # Iniciar los hilos
    hilo1.start()
    hilo2.start()

    # Esperar a que ambos hilos terminen
    hilo1.join()
    hilo2.join()
    # Iniciar la captura de imágenes
    print("Termine")
