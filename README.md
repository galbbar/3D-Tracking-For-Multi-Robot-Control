# 3D Tracking for Multi-Robot Control

## Project overview

This repository implements a prototype pipeline for detecting a sports ball in stereo images, estimating its 3D position, counting fingers using hand detection, and publishing those values over MQTT for use in a multi-robot control system. The project combines camera calibration (single and stereo), a YOLOv8-based ball detector, MediaPipe for hand/finger counting, and a ZED camera acquisition & processing loop.

The codebase was written as a research / prototype implementation and contains the following high-level capabilities:

- Camera intrinsic calibration (per-camera) using chessboard images (`calibration/individual_calibration.py`).
- Stereo calibration to compute rotation and translation between two cameras (`calibration/stereo_calibration.py`).
- Detection of a sports ball using YOLOv8 and triangulation for 3D position estimation (`src/yolo_detector.py`).
- Hand and finger counting using MediaPipe landmarks (`src/mediapipe_detector.py`).
- A ZED2 capture/processing loop that acquires synchronized left/right frames, runs detectors and publishes results over MQTT (`src/main.py`).
- Simple MQTT client wrapper for publishing finger counts and 3D positions (`src/communication/mqtt_client.py`).

## What was done / accomplishments

- Implemented a camera calibration flow: single-camera calibration (chessboard) and stereo calibration (rotation, translation, essential and fundamental matrices).
- Integrated a YOLOv8 model (Ultralytics) to detect the sports ball in each stereo image and triangulate the ball's 3D coordinates using the computed projection matrices.
- Integrated MediaPipe Hands to detect a right hand and count the number of extended fingers.
- Created a threaded ZED camera acquisition and processing pipeline that saves images from the left/right views and simultaneously processes them to detect hands and balls.
- Implemented an MQTT client to publish the 3D position and finger count in plain text for use by other systems (e.g., robot controllers).

## Repository structure

- `calibration/` - Camera calibration utilities
	- `individual_calibration.py` - single camera chessboard calibration and save/load helpers
	- `stereo_calibration.py` - stereo calibration that uses saved single-camera calibrations
- `data/` - datasets, calibration files, models and captured images
	- `calibration/` - contains saved `.npy` calibration files (`stereo_calib.npy`, `left_calib.npy`, `right_calib.npy`)
	- `model/` - contains the YOLOv8 model (`yolov8n.pt`)
	- `captures/` - place to store captured left/right image sequences
- `src/` - main application code
	- `main.py` - ZED camera acquisition and processing loop (entry point)
	- `yolo_detector.py` - YOLOv8-based ball detector and stereo triangulation
	- `mediapipe_detector.py` - MediaPipe-based hand detection & finger counting
	- `communication/mqtt_client.py` - MQTT helper to publish messages

## Key implementation notes

- YOLO model: `src/yolo_detector.py` loads the model from `data/model/yolov8n.pt` using `ultralytics.YOLO`.
- Camera intrinsics: `data/calibration/left/left_calib.npy` and `data/calibration/right/right_calib.npy` are expected to hold saved dictionaries with keys `'camera_matrix'` and `'dist_coeffs'` (created by `CalibradorCamara.calibrar`).
- Stereo params: `data/calibration/stereo_calib.npy` stores stereo parameters saved by `CalibradorEstereo.calibrar` with keys `R`, `T`, `E`, `F`.
- Triangulation: The detector constructs projection matrices `P1` and `P2` and calls OpenCV's `cv2.triangulatePoints` to estimate a 3D point from left/right image centroids.
- Hand detection: `mediapipe` is used in static-image mode to process saved frames and count extended fingers of the right hand; results are drawn on the image for debugging.
- MQTT: `src/communication/mqtt_client.py` uses `paho-mqtt` to connect to `broker.emqx.io:1883` (default) and publishes on topics `v3d/position` and `v3d/finger`.
- ZED: `src/main.py` expects a ZED camera and uses the Stereolabs Python API (`pyzed.sl`) to capture left/right frames. If you don't have a ZED camera you can adapt the acquisition part to use any stereo image source or pre-recorded pairs.

## Dependencies

Core Python packages used by the project (additionally the ZED SDK is required if using a ZED camera):

- Python 3.8+
- numpy
- opencv-python
- ultralytics (YOLOv8)
- mediapipe
- paho-mqtt
- (Stereolabs ZED SDK / pyzed) — manual install required when using `src/main.py` with a ZED camera

I added a minimal `requirements.txt` with the pip-installable pieces (see repository root).

## Installation (Windows PowerShell example)

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

3. ZED SDK (optional if using `src/main.py`):

- Download and install the Stereolabs ZED SDK for Windows from https://www.stereolabs.com/developers/ and follow their installation instructions.
- Ensure the Python bindings for the ZED SDK are available (they are typically installed along with the SDK) so that `import pyzed.sl as sl` works.

## Preparing data and calibration

1. Place your YOLO model at `data/model/yolov8n.pt` (this repository contains a model snapshot in `data/model/`).
2. Collect chessboard images for each camera and put them in two folders (e.g. `data/calibration_images/left/` and `data/calibration_images/right/`).
3. Run single-camera calibration for each camera using `CalibradorCamara.calibrar` (example usage from Python):

```python
from calibration.individual_calibration import CalibradorCamara

# Calibrate left
CalibradorCamara().calibrar('path/to/left/images', 'data/calibration/left/left_calib.npy')

# Calibrate right
CalibradorCamara().calibrar('path/to/right/images', 'data/calibration/right/right_calib.npy')
```

4. Run stereo calibration to compute `R`, `T`, etc.:

```python
from calibration.stereo_calibration import CalibradorEstereo

CalibradorEstereo().calibrar(
		left_calib_path='data/calibration/left/left_calib.npy',
		right_calib_path='data/calibration/right/right_calib.npy',
		folder_left='path/to/left/images',
		folder_right='path/to/right/images',
		save_path='data/calibration/stereo_calib.npy'
)
```

After successful calibration you should have the following `.npy` files in `data/calibration/`:

- `left/left_calib.npy` — single-camera intrinsics for left camera
- `right/right_calib.npy` — single-camera intrinsics for right camera
- `stereo_calib.npy` — stereo rotation `R` and translation `T` (plus `E` and `F`)

## Running the main pipeline

`src/main.py` is the current entry point that captures frames from a ZED camera, saves left/right images, runs the hand and ball detectors, and publishes results via MQTT.

Before running:

- Ensure `data/model/yolov8n.pt` exists.
- Ensure the calibration files in `data/calibration/` are present and valid.

Run with Python (from repository root):

```powershell
python src\main.py
```

Notes:
- The script uses two background threads: one for capturing images from the ZED camera and one for processing saved image pairs.
- Processing publishes the detected finger count and the estimated 3D position (x y z) on MQTT topics. If either detector fails the script prints a diagnostic message and continues.

## Expected output

- MQTT messages on `v3d/position` (payload: "x y z") and `v3d/finger` (payload: finger_count).
- Saved captures in `data/captures/images_left/` and `data/captures/images_right/` during acquisition.

## Troubleshooting

- If OpenCV cannot read images, check the capture paths and that the camera is accessible.
- If YOLO does not detect the ball, verify the model file and check confidence thresholds (the prototype currently accepts any detected `sports ball`).
- If MediaPipe does not detect hands, ensure the frames contain a clear right hand in view and try increasing image resolution.
- If `pyzed.sl` import fails, install the Stereolabs ZED SDK and verify Python bindings.

## Next steps / improvements

- Add confidence filtering and non-max suppression tuning for YOLO detection.
- Add unit tests around triangulation and calibration utilities.
- Add a small GUI/visualization to inspect detections and reprojection error.
- Add support for non-ZED cameras by abstracting the capture interface.
- Save published MQTT messages to a log for post-run analysis.
