import cv2
import numpy as np
from typing import Tuple


def assess_quality(image_bgr: np.ndarray) -> Tuple[float, float, float]:
    """Return (sharpness, exposure, face_area_ratio) in range [0,1] where higher is better.
    - sharpness: normalized Laplacian variance
    - exposure: histogram-based exposure score
    - face_area_ratio: caller should crop face for accurate value; if full image, use bbox ratio
    """
    # Sharpness (Laplacian variance)
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness = max(0.0, min(lap_var / 300.0, 1.0))

    # Exposure: ideal mean around 120-150 on 0..255
    mean_intensity = float(np.mean(gray))
    exposure = 1.0 - (abs(mean_intensity - 135.0) / 135.0)
    exposure = max(0.0, min(exposure, 1.0))

    # Face area ratio cannot be known here; caller passes cropped face to estimate ~1.0
    face_area_ratio = 1.0
    return sharpness, exposure, face_area_ratio


def passes_quality(sharpness: float, exposure: float, face_area_ratio: float,
                   min_sharpness: float = 0.25,
                   min_exposure: float = 0.35,
                   min_face_area_ratio: float = 0.10) -> bool:
    return (
        sharpness >= min_sharpness and
        exposure >= min_exposure and
        face_area_ratio >= min_face_area_ratio
    )


