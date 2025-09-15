from typing import Tuple
import numpy as np


class DummyLivenessModel:
    """CPU-only lightweight liveness scorer placeholder.
    Returns probability of being real in [0,1]. Replace with Torch/TF model as needed.
    """
    def __init__(self) -> None:
        pass

    def predict_proba(self, face_rgb: np.ndarray) -> float:
        # Heuristic: strong moiré/edge scarcity in high-frequency → likely spoof
        import cv2
        gray = cv2.cvtColor(face_rgb, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 80, 160)
        edge_density = float(np.sum(edges > 0)) / float(edges.size)
        # More edges → more likely real
        score = max(0.0, min((edge_density - 0.02) / 0.15, 1.0))
        return score


_MODEL = DummyLivenessModel()


def liveness_score(face_rgb: np.ndarray) -> float:
    return float(_MODEL.predict_proba(face_rgb))


def passes_liveness(score: float, min_score: float = 0.55) -> bool:
    return score >= min_score


