from individual_calibration import CalibradorCamara
from stereo_calibration import CalibradorEstereo
import os

if __name__ == "__main__":
    chessboard_size = (8, 6)
    left_folder = "../data/calibration/left"
    right_folder = "../data/calibration/right"
    left_calib_file = os.path.join(left_folder, "left_calib.npy")
    right_calib_file = os.path.join(right_folder, "right_calib.npy")

    # Calibración individual
    cam_calib = CalibradorCamara(chessboard_size)
    cam_calib.calibrar(left_folder, left_calib_file)
    cam_calib.calibrar(right_folder, right_calib_file)

    # Calibración estéreo
    stereo_calib = CalibradorEstereo(chessboard_size)
    stereo_calib.calibrar(left_calib_file, right_calib_file, left_folder, right_folder)
