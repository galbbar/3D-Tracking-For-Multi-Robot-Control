import cv2
import mediapipe as mp

class FingerCounter:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5
        )

    def count_fingers(self, image_path):
        """
        Procesa una imagen de OpenCV y devuelve una lista con los conteos de dedos por mano.
        También devuelve la imagen anotada con los puntos dibujados.
        """
        image = cv2.imread(image_path)
        if image is None:
            return [], image

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        resultados = self.hands.process(rgb)

        if resultados.multi_hand_landmarks:
            for idx, hand_info in enumerate(resultados.multi_handedness):
                hand_label = hand_info.classification[0].label
                if hand_label == 'Right':
                    hand_landmarks = resultados.multi_hand_landmarks[idx]

                    # Dibuja anotaciones de la mano
                    self.mp_drawing.draw_landmarks(
                        image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                    # Contar dedos
                    count = self.count_from_landmarks(hand_landmarks, hand_label)
                    return count, image
        return 0, None

    def count_from_landmarks(self, hand_landmarks, hand_label):
        tips_ids = [4, 8, 12, 16, 20]
        pip_ids = [3, 6, 10, 14, 18]
        coords = [(lm.x, lm.y) for lm in hand_landmarks.landmark]

        dedos_abiertos = 0
        tip_x, _ = coords[tips_ids[0]]
        pip_x, _ = coords[pip_ids[0]]

        if hand_label == 'Right':
            if tip_x > pip_x:
                dedos_abiertos += 1
        else:
            if tip_x < pip_x:
                dedos_abiertos += 1

        for i in range(1, 5):
            tip_y = coords[tips_ids[i]][1]
            pip_y = coords[pip_ids[i]][1]
            if tip_y < pip_y:
                dedos_abiertos += 1

        return dedos_abiertos

    def close(self):
        self.hands.close()
