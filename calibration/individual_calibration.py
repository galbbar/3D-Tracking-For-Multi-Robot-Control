import cv2
import numpy as np
import os
import glob

class CalibradorCamara:
    def __init__(self, chessboard_size=(8, 6)):
        self.chessboard_size = chessboard_size

    def calibrar(self, image_folder, save_path):
        nx, ny = self.chessboard_size
        objp = np.zeros((nx * ny, 3), np.float32)
        objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)

        objpoints, imgpoints = [], []
        images = sorted(
            sum([glob.glob(os.path.join(image_folder, f'*.{e}')) for e in ('jpg', 'png', 'bmp')], [])
        )
        if not images:
            print(f"❌ No hay imágenes en {image_folder}")
            return None, None

        flags = (cv2.CALIB_CB_ADAPTIVE_THRESH |
                 cv2.CALIB_CB_NORMALIZE_IMAGE |
                 cv2.CALIB_CB_FAST_CHECK)

        for fname in images:
            img = cv2.imread(fname)
            if img is None:
                print(f"⚠️ No pude leer {fname}")
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (nx, ny), flags)

            if ret:
                cv2.cornerSubPix(
                    gray, corners, winSize=(11, 11), zeroZone=(-1, -1),
                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
                )
                objpoints.append(objp)
                imgpoints.append(corners)
                cv2.drawChessboardCorners(img, (nx, ny), corners, ret)
                cv2.imshow('Esquinas detectadas', img)
                cv2.waitKey(100)

        cv2.destroyAllWindows()

        if not objpoints:
            print("❌ No se detectaron esquinas. Abortando.")
            return None, None

        ret, K, D, _, _ = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        print(f"✅ RMS error: {ret:.4f}")

        np.save(save_path, {'camera_matrix': K, 'dist_coeffs': D})
        print(f"📁 Guardado en {save_path}")
        return K, D

    @staticmethod
    def cargar_calibracion(calib_path):
        data = np.load(calib_path, allow_pickle=True).item()
        return data['camera_matrix'], data['dist_coeffs']
