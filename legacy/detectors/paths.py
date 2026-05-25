from pathlib import Path


LEGACY_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = LEGACY_ROOT / "models"
SHAPE_PREDICTOR_MODEL = MODEL_ROOT / "shape_predictor_model" / "shape_predictor_68_face_landmarks.dat"
OBJECT_DETECTION_MODEL = MODEL_ROOT / "object_detection_model"
