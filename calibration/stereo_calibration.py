import cv2
import numpy as np
import os
import glob
from individual_calibration import CalibradorCamara

class CalibradorEstereo:
    def __init__(self, chessboard_size=(8, 6)):
        self.chessboard_size = chessboard_size

    def _obtener_puntos_estereo(self, folder_left, folder_right):
        nx, ny = self.chessboard_size
        objp = np.zeros((nx * ny, 3), np.float32)
        objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)

        objpoints, imgpoints_l, imgpoints_r = [], [], []
        left_images, right_images = [], []

        for ext in ('jpg', 'png', 'bmp'):
            left_images.extend(sorted(glob.glob(os.path.join(folder_left, f'*.{ext}'))))
            right_images.extend(sorted(glob.glob(os.path.join(folder_right, f'*.{ext}'))))

        for l_img, r_img in zip(left_images, right_images):
            img_l = cv2.imread(l_img)
            img_r = cv2.imread(r_img)
            if img_l is None or img_r is None:
                continue

            gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
            gray_r = cv2.cvtColor(img_r, cv2.COLOR_BGR2GRAY)

            ret_l, corners_l = cv2.findChessboardCorners(gray_l, (nx, ny), None)
            ret_r, corners_r = cv2.findChessboardCorners(gray_r, (nx, ny), None)

            if ret_l and ret_r:
                objpoints.append(objp)
                imgpoints_l.append(corners_l)
                imgpoints_r.append(corners_r)

                cv2.drawChessboardCorners(img_l, (nx, ny), corners_l, ret_l)
                cv2.drawChessboardCorners(img_r, (nx, ny), corners_r, ret_r)
                cv2.imshow("Left", img_l)
                cv2.imshow("Right", img_r)
                cv2.waitKey(100)

        cv2.destroyAllWindows()

        if not objpoints:
            print("❌ No se encontraron pares válidos de esquinas estéreo.")
            return None, None, None, None

        return objpoints, imgpoints_l, imgpoints_r, gray_l.shape[::-1]

    def calibrar(self, left_calib_path, right_calib_path, folder_left, folder_right, save_path="./data/calibration/stereo_calib.npy"):
        K1, D1 = CalibradorCamara.cargar_calibracion(left_calib_path)
        K2, D2 = CalibradorCamara.cargar_calibracion(right_calib_path)

        objpoints, imgpoints_l, imgpoints_r, img_shape = self._obtener_puntos_estereo(folder_left, folder_right)
        if objpoints is None:
            return

        flags = cv2.CALIB_FIX_INTRINSIC
        criteria = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 100, 1e-5)

        ret, _, _, _, _, R, T, E, F = cv2.stereoCalibrate(
            objpoints, imgpoints_l, imgpoints_r,
            K1, D1, K2, D2, img_shape,
            criteria=criteria, flags=flags)

        print(f"✅ RMS Error estéreo: {ret}")
        print("🔄 Rotación:\n", R)
        print("➡️ Translación:\n", T)
        print("🎯 Matriz esencial:\n", E)
        print("📐 Matriz fundamental:\n", F)

        np.save(save_path, {'R': R, 'T': T, 'E': E, 'F': F})
        print(f"📁 Parámetros estéreo guardados en {save_path}")
