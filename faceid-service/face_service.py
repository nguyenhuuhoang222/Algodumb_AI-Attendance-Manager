import cv2
import numpy as np
from PIL import Image
import io
import logging
import base64
from typing import Dict, Tuple, Optional, List
import os
import time

logger = logging.getLogger(__name__)

class FaceService:
    def __init__(self):
        self.cv2 = cv2
        self.recognizer = self._initialize_recognizer()
        # Feature flags
        self.enable_quality = os.getenv("FACE_ENABLE_QUALITY", "true").lower() == "true"
        self.enable_pose = os.getenv("FACE_ENABLE_POSE", "true").lower() == "true"
        self.enable_liveness = os.getenv("FACE_ENABLE_LIVENESS", "true").lower() == "true"
        self.enable_mask = os.getenv("FACE_ENABLE_MASK", "true").lower() == "true"
        self.block_strict = os.getenv("FACE_BLOCK_STRICT", "true").lower() == "true"
        # Tunable thresholds (can be adjusted via env)
        def _f(name: str, default: float) -> float:
            try:
                return float(os.getenv(name, str(default)))
            except Exception:
                return default
        # Import threshold configuration
        try:
            from thresholds_config import (
                POSE_MAX_YAW, POSE_MAX_PITCH, POSE_MAX_ROLL,
                QUALITY_MIN_SHARPNESS, QUALITY_MIN_EXPOSURE, QUALITY_MIN_AREA,
                LIVENESS_MIN_SCORE, LIVENESS_TOLERANCE,
                MASK_CONF_THRESHOLD, MASK_SKIN_RATIO_THRESHOLD, MASK_CONSECUTIVE_FRAMES
            )
            # Use config values as defaults
            self.pose_max_yaw = _f("FACE_POSE_MAX_YAW", POSE_MAX_YAW)
            self.pose_max_pitch = _f("FACE_POSE_MAX_PITCH", POSE_MAX_PITCH)
            self.pose_max_roll = _f("FACE_POSE_MAX_ROLL", POSE_MAX_ROLL)
            self.quality_min_sharpness = _f("FACE_QUALITY_MIN_SHARPNESS", QUALITY_MIN_SHARPNESS)
            self.quality_min_exposure = _f("FACE_QUALITY_MIN_EXPOSURE", QUALITY_MIN_EXPOSURE)
            self.quality_min_area = _f("FACE_QUALITY_MIN_AREA", QUALITY_MIN_AREA)
            self.liveness_min_score = _f("FACE_LIVENESS_MIN_SCORE", LIVENESS_MIN_SCORE)
            self.liveness_tolerance = _f("FACE_LIVENESS_TOLERANCE", LIVENESS_TOLERANCE)
            self.mask_conf_threshold = _f("FACE_MASK_CONF_THRESHOLD", MASK_CONF_THRESHOLD)
            self.mask_skin_ratio_threshold = _f("FACE_MASK_SKIN_RATIO_THRESHOLD", MASK_SKIN_RATIO_THRESHOLD)
            self.mask_consecutive_frames = _f("FACE_MASK_CONSECUTIVE_FRAMES", MASK_CONSECUTIVE_FRAMES)
        except ImportError:
            # Fallback to hardcoded values if config file not found
            self.pose_max_yaw = _f("FACE_POSE_MAX_YAW", 60.0)
            self.pose_max_pitch = _f("FACE_POSE_MAX_PITCH", 55.0)
            self.pose_max_roll = _f("FACE_POSE_MAX_ROLL", 55.0)
            self.quality_min_sharpness = _f("FACE_QUALITY_MIN_SHARPNESS", 0.12)
            self.quality_min_exposure = _f("FACE_QUALITY_MIN_EXPOSURE", 0.15)
            self.quality_min_area = _f("FACE_QUALITY_MIN_AREA", 0.05)
            self.liveness_min_score = _f("FACE_LIVENESS_MIN_SCORE", 0.02)
            self.liveness_tolerance = _f("FACE_LIVENESS_TOLERANCE", 0.15)
            self.mask_conf_threshold = _f("FACE_MASK_CONF_THRESHOLD", 0.5)
            self.mask_skin_ratio_threshold = _f("FACE_MASK_SKIN_RATIO_THRESHOLD", 0.25)
            self.mask_consecutive_frames = _f("FACE_MASK_CONSECUTIVE_FRAMES", 3)
    
    def _initialize_recognizer(self):
        """Initialize Insightface model"""
        try:
            from insightface.app import FaceAnalysis
            logger.info("Initializing Insightface model...")
            model = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            model.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("Insightface model initialized successfully")
            return model
        except ImportError:
            raise Exception("Insightface is required. Install with: pip install insightface")
        except Exception as e:
            raise Exception(f"Failed to initialize recognition model: {str(e)}")
    
    # -------------------- Temporal (video) liveness helpers --------------------
    def _laplacian_sharpness(self, img_bgr: np.ndarray) -> float:
        try:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            return float(cv2.Laplacian(gray, cv2.CV_64F).var())
        except Exception:
            return 0.0

    def _pose_from_landmarks5(self, lm5: np.ndarray) -> Tuple[float, float, float]:
        try:
            from validators.pose import estimate_pose_from_landmarks
            yaw, pitch, roll = estimate_pose_from_landmarks(lm5[:5])
            return float(yaw), float(pitch), float(roll)
        except Exception:
            return 0.0, 0.0, 0.0

    def _temporal_liveness_score(self, faces_info: List[Dict[str, np.ndarray]]) -> float:
        """Compute a simple temporal liveness score using yaw variation and eye openness changes.
        faces_info: list of dicts per frame with keys: 'landmarks5' (np.ndarray), 'bbox' (np.ndarray)
        """
        if not faces_info:
            return 0.0
        yaws: List[float] = []
        eye_opens: List[float] = []
        for info in faces_info:
            lm = info.get('landmarks5')
            if isinstance(lm, np.ndarray) and lm.shape[0] >= 5:
                yaw, pitch, roll = self._pose_from_landmarks5(lm)
                yaws.append(yaw)
                # crude eye openness from distance between eye corners (points 0-1 and 2-3 for 5pt)
                try:
                    left_eye = np.linalg.norm(lm[0] - lm[1])
                    right_eye = np.linalg.norm(lm[2] - lm[3])
                    eye_open = float(left_eye + right_eye)
                    eye_opens.append(eye_open)
                except Exception:
                    pass
        # Normalize metrics
        if len(yaws) >= 2:
            yaw_range = float(max(yaws) - min(yaws))
        else:
            yaw_range = 0.0
        if len(eye_opens) >= 2:
            eye_var = float(np.std(eye_opens))
        else:
            eye_var = 0.0
        # Map to 0..1 ranges with gentle ceilings
        yaw_score = min(yaw_range / 10.0, 1.0)  # 10 degrees variation -> 1.0
        blink_score = min(eye_var / 1.5, 1.0)   # heuristic scale
        # Combine with motion prior
        return 0.6 * yaw_score + 0.4 * blink_score
    
    def process_image(self, image_bytes):
        """Process uploaded image with enhanced error handling"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check image properties
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            # Validate image size
            if image.size[0] < 50 or image.size[1] < 50:
                raise Exception("Image is too small for face detection")
            
            image_array = np.array(image)
            
            # Convert to BGR for OpenCV if needed
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image_array
            
            return image_bgr
            
        except Exception as e:
            logger.error(f"Image processing failed: {str(e)}")
            raise Exception(f"Invalid image format: {str(e)}")
    
    def _check_for_mask(self, image: np.ndarray, face_bbox: List[int]) -> Tuple[bool, float]:
        """Check if the detected face might be wearing a mask - IMPROVED VERSION"""
        try:
            x1, y1, x2, y2 = face_bbox
            face_region = image[y1:y2, x1:x2]
            
            if face_region.size == 0:
                return False, 0.0
            
            height, width = face_region.shape[:2]
            
            # Only check lower part of face for masks
            lower_face = face_region[int(height*0.6):, :]
            
            if lower_face.size == 0:
                return False, 0.0
            
            # Convert to different color spaces for better analysis
            gray_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2GRAY)
            hsv_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2HSV)
            ycrcb_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2YCrCb)
            
            # Calculate multiple features
            features = []
            
            # 1. Color variance (masks often have uniform color)
            color_variance = np.var(lower_face)
            features.append(min(color_variance / 500, 1.0))  # Normalize
            
            # 2. Texture analysis (masks have different texture)
            texture_var = cv2.Laplacian(gray_lower, cv2.CV_64F).var()
            features.append(min((100 - texture_var) / 100, 1.0))  # Lower texture = more likely mask
            
            # 3. Saturation analysis (masks often have low saturation)
            saturation_mean = np.mean(hsv_lower[:,:,1])
            features.append(min((50 - saturation_mean) / 50, 1.0))  # Lower saturation = more likely mask
            
            # 4. Edge density (masks may have fewer edges in mouth area)
            edges = cv2.Canny(gray_lower, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size
            features.append(min((0.1 - edge_density) / 0.1, 1.0))  # Fewer edges = more likely mask

            # 5. Skin-tone presence ratio in lower face (very indicative)
            # HSV skin range
            lower_hsv_skin = np.array([0, 30, 60], dtype=np.uint8)
            upper_hsv_skin = np.array([20, 150, 255], dtype=np.uint8)
            hsv_skin_mask = cv2.inRange(hsv_lower, lower_hsv_skin, upper_hsv_skin)

            # YCrCb skin range
            lower_ycrcb_skin = np.array([0, 133, 77], dtype=np.uint8)
            upper_ycrcb_skin = np.array([255, 173, 127], dtype=np.uint8)
            ycrcb_skin_mask = cv2.inRange(ycrcb_lower, lower_ycrcb_skin, upper_ycrcb_skin)

            # Combine masks
            combined_skin_mask = cv2.bitwise_and(hsv_skin_mask, ycrcb_skin_mask)
            skin_ratio = float(np.sum(combined_skin_mask > 0)) / float(combined_skin_mask.size)
            # Lower skin ratio implies mask
            skin_ratio_feature = min((0.35 - skin_ratio) / 0.35, 1.0)  # if <35% skin => likely mask
            features.append(skin_ratio_feature)
            
            # Weighted average with more weight on texture and edges
            weights = [0.18, 0.35, 0.17, 0.15, 0.15]  # Texture and skin ratio emphasized
            mask_confidence = sum(w * f for w, f in zip(weights, features))
            
            # Apply sigmoid-like function; center slightly lower to be more sensitive
            mask_confidence = 1 / (1 + np.exp(-10 * (mask_confidence - 0.45)))
            
            # Hard rule: if skin ratio is very low, immediately flag mask - Increase threshold to detect easier
            if skin_ratio < 0.30:  # Increased from 0.20 to 0.30
                return True, float(max(mask_confidence, 0.85))
            
            # Return positive for moderately strict threshold - Lower threshold to detect easier
            return mask_confidence > 0.4, float(mask_confidence)  # Lowered from 0.6 to 0.4
            
        except Exception as e:
            logger.warning(f"Mask detection check failed: {str(e)}")
            return False, 0.0
    
    def extract_face_embedding(self, image_bytes, min_liveness_override: Optional[float] = None, allow_mask_override: Optional[bool] = None):
        """Extract face embedding using Insightface with IMPROVED mask detection"""
        try:
            # Process image
            image = self.process_image(image_bytes)
            
            # Convert to RGB for Insightface
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect and recognize faces
            faces = self.recognizer.get(rgb_image)
            
            if len(faces) == 0:
                raise Exception("No faces detected in the image")
            
            if len(faces) > 1:
                raise Exception("Multiple faces detected. Please use an image with only one face")
            
            # Get the first face
            face = faces[0]
            bbox = face.bbox.astype(int)
            landmarks = getattr(face, 'landmark_2d_106', None)
            if landmarks is None:
                landmarks = getattr(face, 'landmark_2d_5', None)
            
            scores: Dict[str, float] = {}

            # Extract face crop for validators
            x1, y1, x2, y2 = bbox
            face_region_bgr = image[y1:y2, x1:x2].copy()
            face_region_rgb = cv2.cvtColor(face_region_bgr, cv2.COLOR_BGR2RGB)

            # Quality
            if self.enable_quality:
                from validators.quality import assess_quality, passes_quality
                s, e, a = assess_quality(face_region_bgr)
                scores.update({"quality_sharpness": s, "quality_exposure": e, "quality_area": a})
                if self.block_strict and not passes_quality(
                    s, e, a,
                    min_sharpness=self.quality_min_sharpness,
                    min_exposure=self.quality_min_exposure,
                    min_face_area_ratio=self.quality_min_area,
                ):
                    raise Exception("Image quality too low. Please improve lighting or avoid motion blur.")

            # Pose
            if self.enable_pose and landmarks is not None:
                from validators.pose import estimate_pose_from_landmarks, passes_pose
                lm = landmarks if isinstance(landmarks, np.ndarray) else np.array(landmarks)
                if lm.shape[0] >= 5:
                    yaw, pitch, roll = estimate_pose_from_landmarks(lm[:5])
                    scores.update({"pose_yaw": float(yaw), "pose_pitch": float(pitch), "pose_roll": float(roll)})
                    pose_ok = passes_pose(
                        yaw, pitch, roll,
                        max_yaw=self.pose_max_yaw,
                        max_pitch=self.pose_max_pitch,
                        max_roll=self.pose_max_roll,
                    )
                    if not pose_ok:
                        # Allow small violations; block only when far beyond limits (>1.5x)
                        hard_fail = (
                            abs(yaw) > self.pose_max_yaw * 1.5 or
                            abs(pitch) > self.pose_max_pitch * 1.5 or
                            abs(roll) > self.pose_max_roll * 1.5
                        )
                        logger.warning(
                            f"Pose not ideal (yaw={yaw:.1f}, pitch={pitch:.1f}, roll={roll:.1f}). hard_fail={hard_fail}"
                        )
                        if self.block_strict and hard_fail:
                            raise Exception("Face pose out of range. Please look straight at the camera.")

            # Liveness
            if self.enable_liveness:
                from validators.liveness import liveness_score, passes_liveness
                lv = liveness_score(face_region_rgb)
                scores["liveness"] = float(lv)
                min_live = float(min_liveness_override) if (min_liveness_override is not None) else self.liveness_min_score
                # Allow larger tolerance to avoid boundary false rejects - using config
                eff_min = max(0.0, min_live - getattr(self, 'liveness_tolerance', 0.15))
                ok_live = passes_liveness(lv, min_score=eff_min)
                if not ok_live:
                    msg = (
                        f"Spoof/liveness failed (score={lv:.2f} < min {min_live:.2f}). "
                        "Please use a live face, not a photo/screen."
                    )
                    if self.block_strict:
                        raise Exception(msg)
                    else:
                        logger.warning(msg)

            # Mask
            if self.enable_mask and not bool(allow_mask_override):
                has_mask, mask_confidence = self._check_for_mask(image, bbox)
                scores["mask_confidence"] = float(mask_confidence)
                # Apply custom threshold as additional rule
                if has_mask or (mask_confidence > self.mask_conf_threshold):
                    logger.warning(
                        f"Mask detected. det_score={getattr(face, 'det_score', None)}, confidence={mask_confidence:.2f}"
                    )
                    raise Exception(
                        f"Face mask detected (confidence: {mask_confidence:.2f}). Please remove mask for recognition."
                    )
            
            # Extract face region for debugging
            x1, y1, x2, y2 = bbox
            face_region = image[y1:y2, x1:x2].copy()
            
            # Convert face region to base64
            _, img_buffer = cv2.imencode('.jpg', face_region)
            face_image_base64 = base64.b64encode(img_buffer).decode('utf-8')
            
            # Convert embedding to base64
            embedding_base64 = base64.b64encode(face.embedding.tobytes()).decode('utf-8')
            
            return embedding_base64, face_image_base64
            
        except Exception as e:
            logger.error(f"Face embedding extraction failed: {str(e)}")
            raise Exception(f"Face embedding extraction failed: {str(e)}")

    def extract_embedding_from_sequence(self, frames: List[bytes], min_liveness_override: Optional[float] = None, allow_mask_override: Optional[bool] = None) -> Tuple[str, str, Dict[str, float]]:
        """Process a short sequence (0.8–1.0s) of JPEG frames for stronger liveness.
        Returns (embedding_base64, face_image_base64, scores)
        """
        try:
            if not frames or len(frames) < 3:
                raise Exception("Not enough frames for temporal liveness")
            faces_info: List[Dict[str, np.ndarray]] = []
            best_face = None
            best_lap = 0.0
            best_crop_bgr = None
            for b in frames:
                img_bgr = self.process_image(b)
                rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                faces = self.recognizer.get(rgb)
                if not faces:
                    continue
                face = max(faces, key=lambda f: getattr(f, 'det_score', 0.0))
                bbox = face.bbox.astype(int)
                lm5 = getattr(face, 'landmark_2d_5', None)
                if lm5 is None:
                    lm5 = getattr(face, 'landmark_2d_106', None)
                    if isinstance(lm5, np.ndarray) and lm5.shape[0] >= 5:
                        lm5 = lm5[:5]
                if isinstance(lm5, np.ndarray):
                    faces_info.append({'landmarks5': lm5, 'bbox': bbox})
                # track sharpest face crop
                x1, y1, x2, y2 = bbox
                crop = img_bgr[y1:y2, x1:x2]
                lap = self._laplacian_sharpness(crop)
                if lap > best_lap:
                    best_lap = lap
                    best_face = face
                    best_crop_bgr = crop
            if not faces_info or best_face is None or best_crop_bgr is None:
                raise Exception("No faces found across frames")
            # temporal liveness
            tlive = self._temporal_liveness_score(faces_info)
            scores = {'temporal_liveness': float(tlive)}
            min_live = float(min_liveness_override) if (min_liveness_override is not None) else self.liveness_min_score
            eff_min = max(0.0, min_live - 0.10)
            if tlive < eff_min:
                raise Exception(
                    f"Temporal liveness failed (score={tlive:.2f} < min {min_live:.2f})"
                )
            # quality and mask checks on best crop
            if self.enable_quality:
                from validators.quality import assess_quality, passes_quality
                s, e, a = assess_quality(best_crop_bgr)
                scores.update({'quality_sharpness': s, 'quality_exposure': e, 'quality_area': a})
                if self.block_strict and not passes_quality(s, e, a,
                    min_sharpness=self.quality_min_sharpness,
                    min_exposure=self.quality_min_exposure,
                    min_face_area_ratio=self.quality_min_area,
                ):
                    raise Exception("Image quality too low in sequence")
            if self.enable_mask and not bool(allow_mask_override):
                has_mask, mask_conf = self._check_for_mask(best_crop_bgr, best_face.bbox.astype(int))
                scores['mask_confidence'] = float(mask_conf)
                if has_mask or (mask_conf > self.mask_conf_threshold):
                    raise Exception("Mask detected in best frame of sequence")
            # finalize embedding
            embedding_base64 = base64.b64encode(best_face.embedding.tobytes()).decode('utf-8')
            _, img_buf = cv2.imencode('.jpg', best_crop_bgr)
            face_image_base64 = base64.b64encode(img_buf).decode('utf-8')
            return embedding_base64, face_image_base64, scores
        except Exception as e:
            logger.error(f"Sequence embedding extraction failed: {str(e)}")
            raise Exception(f"Sequence embedding extraction failed: {str(e)}")
    
    def compare_embeddings(self, embedding1, embedding2, threshold=None):
        """Compare two face embeddings using cosine similarity"""
        try:
            # Use default threshold if not provided
            if threshold is None:
                from thresholds_config import FACE_SIMILARITY_THRESHOLD
                threshold = FACE_SIMILARITY_THRESHOLD
                
            # Normalize embeddings
            embedding1_norm = embedding1 / np.linalg.norm(embedding1)
            embedding2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1_norm, embedding2_norm)
            
            return similarity > threshold, similarity
        except Exception as e:
            raise Exception(f"Embedding comparison failed: {str(e)}")