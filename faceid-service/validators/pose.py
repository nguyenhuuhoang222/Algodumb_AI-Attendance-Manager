from typing import Tuple
import numpy as np


def estimate_pose_from_landmarks(landmarks: np.ndarray) -> Tuple[float, float, float]:
    """Approximate yaw, pitch, roll from 5-point landmarks (InsightFace format).
    landmarks: shape (5,2)
    Returns (yaw, pitch, roll) in degrees (rough estimate).
    """
    # Simple heuristics: roll from eye slope; yaw from eye-nose asymmetry; pitch from eye-mouth vertical ratio
    left_eye, right_eye, nose, left_mouth, right_mouth = landmarks
    eye_vec = right_eye - left_eye
    roll = float(np.degrees(np.arctan2(eye_vec[1], eye_vec[0])))
    # Normalize roll into [-90, 90] to avoid wrap-around artifacts
    if roll > 90.0:
        roll -= 180.0
    elif roll < -90.0:
        roll += 180.0

    # Yaw: horizontal offset of nose from eye midpoint
    eye_mid = (left_eye + right_eye) / 2.0
    yaw = float((nose[0] - eye_mid[0]) / max(np.linalg.norm(eye_vec), 1e-6)) * 30.0

    # Pitch: vertical distance nose-eye vs mouth-eye
    mouth_mid = (left_mouth + right_mouth) / 2.0
    eye_to_nose = abs(nose[1] - eye_mid[1])
    eye_to_mouth = abs(mouth_mid[1] - eye_mid[1]) + 1e-6
    ratio = eye_to_nose / eye_to_mouth
    pitch = float((ratio - 0.5) * 60.0)

    return yaw, pitch, roll


def passes_pose(yaw: float, pitch: float, roll: float,
                max_yaw: float = 30.0,
                max_pitch: float = 25.0,
                max_roll: float = 25.0) -> bool:
    return abs(yaw) <= max_yaw and abs(pitch) <= max_pitch and abs(roll) <= max_roll


