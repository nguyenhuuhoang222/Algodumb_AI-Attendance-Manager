import cv2
import numpy as np
import time
import logging
from streamlit_webrtc import VideoProcessorBase
import av
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

class ReadinessProcessor(VideoProcessorBase):
    
    def __init__(self):
        self.start_ts = time.time()
        self.scan_timeout_s = 5.0
        self.scan_start_time = None
        self._frame_skip_counter = 0
        
        self.person_timer_start = None
        self.person_timer_duration = 5.0
        self.timer_active = False
        self.timer_expired = False
        
        self.check_timer_start = None
        self.check_timer_duration = 0.8
        self.check_timer_active = False
        self.last_check_timer_start = None
        self.check_timer_cooldown = 1.0
        
        self.face_cascade = None
        self.face_bbox = None
        self.face_size_ratio = 0.0
        self.face_center_offset = (0.5, 0.5)
        self.face_ok = False
        
        self.color_status = "red"
        self.status_changed_to_green = False
        
        self.capturing_best_frame = False
        self.best_frame_capture_start = None
        self.best_frame_capture_duration = 2.0
        
        self.ok_frames = 0
        self.best_frame = None
        self.readiness = 0.0
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'faceid-service'))
            from thresholds_config import READINESS_THRESHOLD, MOTION_FRAMES_REQUIRED, MASK_SKIN_RATIO_THRESHOLD, MASK_CONSECUTIVE_FRAMES
            self.readiness_threshold = READINESS_THRESHOLD
            self.motion_frames_required = MOTION_FRAMES_REQUIRED
            self.mask_skin_ratio_threshold = MASK_SKIN_RATIO_THRESHOLD
            self.mask_consecutive_frames = MASK_CONSECUTIVE_FRAMES
        except ImportError:
            # Fallback to hardcoded values - Tăng ngưỡng phát hiện khẩu trang
            self.readiness_threshold = 0.05
            self.motion_frames_required = 2
            self.mask_skin_ratio_threshold = 0.25  # Tăng từ 0.15 để phát hiện dễ hơn
            self.mask_consecutive_frames = 3       # Hạ từ 5 để phát hiện nhanh hơn
        
        self.prev_gray = None
        self.motion_ok_consec = 0
        self.liveness_ok = False
        self.latest_frame = None
        self.motion_now = False
        self._last_motion_centroid = None
        
        self.challenge = None
        self.challenge_issued_ts = None
        self.challenge_ok = False
        self.last_completed_pose = None
        
        self.mask_suspect_consec = 0
        self.mask_suspect = False
        
        self.status_text = "Aligning face..."
        self.hint = "Position face in frame - look straight - ensure good lighting"
        self.error_text = ""
        
        self.prev_frame_hash = None
        
        self._initialize_face_cascade()
    
    def start_person_timer(self):
        self.person_timer_start = time.time()
        self.timer_active = True
        self.timer_expired = False
        self.status_changed_to_green = False
        self.color_status = "red"
        logger.info("5-second timer started for new person")
    
    def is_timer_active(self):
        if not self.timer_active or self.person_timer_start is None:
            return False
        
        elapsed = time.time() - self.person_timer_start
        if elapsed >= self.person_timer_duration:
            self.timer_expired = True
            self.timer_active = False
            return False
        
        return True
    
    def get_remaining_time(self):
        if not self.timer_active or self.person_timer_start is None:
            return 0
        
        elapsed = time.time() - self.person_timer_start
        remaining = max(0, self.person_timer_duration - elapsed)
        return remaining
    
    def reset_person_timer(self):
        self.person_timer_start = None
        self.timer_active = False
        self.timer_expired = False
        self.status_changed_to_green = False
        self.color_status = "red"
        self.check_timer_start = None
        self.check_timer_active = False
        self.last_check_timer_start = None
        logger.info("Timer has been reset for the next person")
    
    def start_check_timer(self):
        self.check_timer_start = time.time()
        self.last_check_timer_start = time.time()
        self.check_timer_active = True
        logger.info("0.8-second check timer started")
    
    def is_check_timer_active(self):
        if not self.check_timer_active or self.check_timer_start is None:
            return False
        
        elapsed = time.time() - self.check_timer_start
        if elapsed >= self.check_timer_duration:
            self.check_timer_active = False
            return False
        
        return True
    
    def get_check_remaining_time(self):
        if not self.check_timer_active or self.check_timer_start is None:
            return 0
        
        elapsed = time.time() - self.check_timer_start
        remaining = max(0, self.check_timer_duration - elapsed)
        return remaining
    
    def can_start_check_timer(self):
        if self.last_check_timer_start is None:
            return True
        
        elapsed_since_last = time.time() - self.last_check_timer_start
        return elapsed_since_last >= self.check_timer_cooldown
    
    def start_best_frame_capture(self):
        logger.info(f"Starting best frame capture - current status: capturing={self.capturing_best_frame}, best_frame={self.best_frame is not None}")
        self.capturing_best_frame = True
        self.best_frame_capture_start = time.time()
        self.best_frame = None
        logger.info("Starting best frame capture - requesting person to stand still")
    
    def is_capturing_best_frame(self):
        if not self.capturing_best_frame or self.best_frame_capture_start is None:
            return False
        
        elapsed = time.time() - self.best_frame_capture_start
        if elapsed >= self.best_frame_capture_duration:
            self.capturing_best_frame = False
            return False
        
        return True
    
    def get_best_frame_remaining_time(self):
        if not self.capturing_best_frame or self.best_frame_capture_start is None:
            return 0
        
        elapsed = time.time() - self.best_frame_capture_start
        remaining = max(0, self.best_frame_capture_duration - elapsed)
        return remaining

    def _initialize_face_cascade(self):
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            if self.face_cascade.empty():
                raise Exception("Failed to load face cascade")
        except Exception as e:
            logger.error(f"Face cascade initialization failed: {str(e)}")
            self.face_cascade = None
    
    def start_scan_timeout(self):
        self.scan_start_time = time.time()
    
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        try:
            img = frame.to_ndarray(format="bgr24")
            self.latest_frame = img.copy()
            
            self._frame_skip_counter += 1
            if self._frame_skip_counter % 3 != 0:
                return frame
            
            if self.is_timer_active():
                self._process_frame(img)
                
                if (not self.is_check_timer_active() and 
                    self.face_ok and 
                    self.can_start_check_timer() and
                    not (self.color_status == "green" and self.best_frame is not None)):
                    self.start_check_timer()
                
                self._update_color_status()
                
                if (self.color_status == "green" and 
                    self.best_frame is not None and 
                    self.is_check_timer_active()):
                    self.check_timer_active = False
                    logger.info("GREEN and best frame obtained - stopping 0.8s timer, moving to next step!")
                
                if self.get_remaining_time() <= 0:
                    if not self.timer_expired:
                        self.timer_expired = True
                        self.status_text = "Scan time expired! Please try again."
                        self.hint = "5-second timer has expired. Press the button to restart."
                        self.color_status = "red"
                        logger.warning("Timer expired - 5 seconds completed")
                    else:
                        if not hasattr(self, 'timer_reset_time'):
                            self.timer_reset_time = time.time()
                        elif time.time() - self.timer_reset_time > 2.0:
                            self._reset_timer_for_next_person()
                            logger.info("Timer reset for next person")
                
                elif self.get_remaining_time() < 0.5:
                    if not self.liveness_ok:
                        self.timer_expired = True
                        self.status_text = "Liveness check failed! Please move your head slightly."
                        self.hint = "System did not detect movement. Please try again."
                        self.color_status = "red"
                        logger.warning("Timer expired due to liveness failure")
                    elif self.mask_suspect:
                        self.timer_expired = True
                        self.status_text = "Mask detected! Please remove your mask."
                        self.hint = "System detected a mask. Please remove your mask and try again."
                        self.color_status = "red"
                        logger.warning("Timer expired due to mask detection")
                    elif not self.face_ok:
                        self.timer_expired = True
                        self.status_text = "No face detected! Please place your face in the frame."
                        self.hint = "System did not detect a clear face. Please adjust your position."
                        self.color_status = "red"
                        logger.warning("Timer expired due to no face detected")
                    elif self.readiness < 0.1:
                        self.timer_expired = True
                        self.status_text = "Face quality too low! Please improve conditions."
                        self.hint = "Lighting or angle is not suitable. Please adjust."
                        self.color_status = "red"
                        logger.warning("Timer expired due to low face quality")
                
            elif self.timer_expired:
                self.status_text = "Time expired! Please try again."
                self.hint = "5-second timer has expired. Press the button to restart."
                self.color_status = "red"
            else:
                self._detect_face(img)
                if self.face_ok:
                    self.start_person_timer()
                    self._process_frame(img)
                else:
                    self.status_text = "Place your face in the frame to start the timer"
                    self.hint = "When a face is detected, the 5-second timer will start"
                    self.color_status = "red"
            
            img_with_overlay = self._draw_overlay(img)
            
            return av.VideoFrame.from_ndarray(img_with_overlay, format="bgr24")
            
        except Exception as e:
            logger.error(f"Frame processing error: {str(e)}")
            self.error_text = f"Processing error: {str(e)}"
            return frame
    
    def _process_frame(self, img: np.ndarray):
        try:
            self._detect_face(img)
            
            if self.face_ok:
                face_crop = self._extract_face_crop(img)
                
                if face_crop is not None:
                    self._assess_quality(face_crop)
                    
                    self._check_liveness(face_crop)
                    
                    self._detect_mask(face_crop)
                    
                    self._calculate_readiness()
                    
                    self._update_best_frame(img)
            
            self._update_status_text()
            
        except Exception as e:
            logger.error(f"Frame processing failed: {str(e)}")
            self.error_text = f"Processing failed: {str(e)}"
    
    def _detect_face(self, img: np.ndarray):
        if self.face_cascade is None:
            logger.warning("Face cascade not initialized")
            self.face_ok = False
            return
        
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.05,
                minNeighbors=3,
                minSize=(30, 30)
            )
            
            logger.debug(f"Face detection: found {len(faces)} faces")
            
            if len(faces) == 0:
                self.face_ok = False
                self.face_bbox = None
                return
            
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            self.face_bbox = (x, y, w, h)
            
            img_h, img_w = img.shape[:2]
            self.face_size_ratio = (w * h) / (img_w * img_h)
            
            face_center_x = (x + w/2) / img_w
            face_center_y = (y + h/2) / img_h
            self.face_center_offset = (face_center_x, face_center_y)
            
            size_ok = 0.02 <= self.face_size_ratio <= 0.6
            center_ok = 0.2 <= face_center_x <= 0.8 and 0.2 <= face_center_y <= 0.8
            
            self.face_ok = size_ok and center_ok
            
            logger.debug(f"Face detection: size_ratio={self.face_size_ratio:.3f}, center=({face_center_x:.3f}, {face_center_y:.3f})")
            logger.debug(f"Face requirements: size_ok={size_ok}, center_ok={center_ok}, face_ok={self.face_ok}")
            
        except Exception as e:
            logger.error(f"Face detection failed: {str(e)}")
            self.face_ok = False
    
    def _extract_face_crop(self, img: np.ndarray) -> Optional[np.ndarray]:
        if not self.face_ok or self.face_bbox is None:
            return None
        
        try:
            x, y, w, h = self.face_bbox
            padding = int(min(w, h) * 0.2)
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(img.shape[1], x + w + padding)
            y2 = min(img.shape[0], y + h + padding)
            
            return img[y1:y2, x1:x2]
        except Exception as e:
            logger.error(f"Face crop extraction failed: {str(e)}")
            return None
    
    def _assess_quality(self, face_crop: np.ndarray):
        try:
            gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness = min(laplacian_var / 1000.0, 1.0)
            
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            exposure = np.sum(hist[50:200]) / np.sum(hist)
            
            area_ratio = self.face_size_ratio
            
            quality_score = (sharpness * 0.4 + exposure * 0.3 + area_ratio * 0.3)
            self.readiness = min(quality_score, 1.0)
            
            if quality_score > 0.3:
                self.ok_frames += 1
            else:
                self.ok_frames = max(0, self.ok_frames - 1)
                
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            self.readiness = 0.0
    
    def _check_liveness(self, face_crop: np.ndarray):
        try:
            gray_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            
            if self.prev_gray is not None and self.prev_gray.shape == gray_crop.shape:
                diff = cv2.absdiff(gray_crop, self.prev_gray)
                motion = float(diff.mean()) / 255.0
                
                if motion > 0.001:
                    self.motion_ok_consec += 1
                else:
                    self.motion_ok_consec = max(0, self.motion_ok_consec - 1)
                
                self.motion_now = motion > 0.005
            
            if self._frame_skip_counter % 3 == 0:
                self.prev_gray = gray_crop
            
            now = time.time()
            if (self.challenge is None and 
                self.readiness >= self.readiness_threshold and 
                self.face_ok):
                
                if (self.challenge_issued_ts is None or 
                    now - self.challenge_issued_ts > 1.0):
                    self.challenge = 'motion'
                    self.challenge_issued_ts = now
                    self.challenge_ok = False
                    self.hint = "Slightly move your head to verify liveness"
            
            if self.challenge == 'motion' and not self.challenge_ok:
                if self.motion_ok_consec >= 2:
                    self.challenge_ok = True
                    self.last_completed_pose = 'motion'
            
            frame_variation_ok = True
            if self.prev_frame_hash is not None:
                current_hash = hash(face_crop.tobytes())
                frame_variation_ok = (current_hash != self.prev_frame_hash)
            self.prev_frame_hash = hash(face_crop.tobytes())
            
            self.liveness_ok = (self.motion_ok_consec >= 1) or (self.motion_ok_consec >= 1 and self.challenge_ok)
            
        except Exception as e:
            logger.error(f"Liveness check failed: {str(e)}")
            self.liveness_ok = False
    
    def _update_color_status(self):
        try:
            logger.debug(f"Updating color status - readiness: {self.readiness:.3f}, threshold: {self.readiness_threshold:.3f}")
            logger.debug(f"Liveness: {self.liveness_ok}, no_mask: {not self.mask_suspect}, current_status: {self.color_status}")
            
            if self.readiness >= self.readiness_threshold and self.liveness_ok and not bool(self.mask_suspect):
                if self.color_status != "green":
                    self.color_status = "green"
                    self.status_changed_to_green = True
                    self.start_best_frame_capture()
                    logger.info("Status changed to GREEN - starting best frame capture!")
                else:
                    if not self.is_capturing_best_frame() and self.best_frame is None:
                        self.start_best_frame_capture()
                        logger.info("Already green but not captured - starting best frame capture!")
            elif self.readiness >= self.readiness_threshold * 0.7:
                if self.color_status != "yellow":
                    self.color_status = "yellow"
            else:
                if self.color_status != "red":
                    self.color_status = "red"
        except Exception as e:
            logger.error(f"Color status update failed: {str(e)}")
            self.color_status = "red"

    def _detect_mask(self, face_crop: np.ndarray):
        try:
            if self._frame_skip_counter % 4 != 0:
                return
            
            h, w = face_crop.shape[:2]
            lower_half = face_crop[int(h*0.6):, :]
            
            if lower_half.size > 0:
                hsv = cv2.cvtColor(lower_half, cv2.COLOR_BGR2HSV)
                ycrcb = cv2.cvtColor(lower_half, cv2.COLOR_BGR2YCrCb)
                
                hsv_mask = cv2.inRange(hsv, (0, 30, 60), (20, 150, 255))
                ycrcb_mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
                skin_mask = cv2.bitwise_and(hsv_mask, ycrcb_mask)
                
                skin_ratio = float(np.sum(skin_mask > 0)) / float(skin_mask.size)
                
                skin_threshold = getattr(self, 'mask_skin_ratio_threshold', 0.15)
                if skin_ratio < skin_threshold:
                    self.mask_suspect_consec += 1
                else:
                    self.mask_suspect_consec = max(0, self.mask_suspect_consec - 2)
            
            consecutive_threshold = getattr(self, 'mask_consecutive_frames', 5)
            self.mask_suspect = self.mask_suspect_consec >= consecutive_threshold
            
        except Exception as e:
            logger.error(f"Mask detection failed: {str(e)}")
            self.mask_suspect = False
    
    def _calculate_readiness(self):
        if self.mask_suspect:
            self.readiness = 0.0
            return
        
        if self.scan_start_time is not None:
            elapsed = time.time() - self.scan_start_time
            if elapsed > self.scan_timeout_s:
                self.readiness = 0.0
                return
        
        elapsed = time.time() - self.start_ts
        if elapsed < 2.0:
            min_quality = 0.4
        else:
            min_quality = 0.6
        
        if (self.face_ok and 
            self.readiness >= min_quality and 
            self.liveness_ok and 
            not self.mask_suspect):
            self.readiness = min(self.readiness, 1.0)
        else:
            self.readiness = max(0.0, self.readiness * 0.9)
        
        logger.debug(f"Readiness calculation: face_ok={self.face_ok}, liveness_ok={self.liveness_ok}, mask_suspect={self.mask_suspect}")
        logger.debug(f"Readiness result: {self.readiness:.3f}, min_quality={min_quality:.3f}")
    
    def _update_best_frame(self, img: np.ndarray):
        if (self.is_capturing_best_frame() and
            self.readiness > 0.3 and
            (self.best_frame is None or self.readiness > getattr(self, '_best_readiness', 0))):
            self.best_frame = img.copy()
            self._best_readiness = self.readiness
            logger.debug(f"Updated best_frame with readiness: {self.readiness:.3f} (capturing mode)")
            
            if self.readiness >= 0.6:
                self.capturing_best_frame = False
                logger.info(f"Best frame captured early - high quality detected! Readiness: {self.readiness:.3f}")
    
    def _update_status_text(self):
        if not self.face_ok:
            self.status_text = "No face detected"
            self.hint = "Position your face in the camera frame"
        elif self.mask_suspect:
            self.status_text = "Please remove mask"
            self.hint = "Remove any face covering for better recognition"
        elif not self.liveness_ok:
            self.status_text = "Move slightly to verify liveness"
            self.hint = "Slightly move your head or blink"
        elif self.readiness < self.readiness_threshold:
            self.status_text = "Improving quality..."
            self.hint = "Hold still, ensure good lighting"
        else:
            self.status_text = "Ready for capture"
            self.hint = "Face detected and ready"
    
    def _draw_overlay(self, img: np.ndarray) -> np.ndarray:
        try:
            overlay = img.copy()
            h, w = img.shape[:2]
            
            self._draw_timer_info(overlay, w, h)
            
            if self.face_ok and self.face_bbox is not None:
                x, y, w_face, h_face = self.face_bbox
                
                if self.color_status == "green":
                    color = (0, 255, 0)
                elif self.color_status == "yellow":
                    color = (0, 255, 255)
                else:
                    color = (0, 0, 255)
                
                cv2.rectangle(overlay, (x, y), (x + w_face, y + h_face), color, 3)
                
                center_x = x + w_face // 2
                center_y = y + h_face // 2
                cv2.line(overlay, (center_x - 15, center_y), (center_x + 15, center_y), color, 2)
                cv2.line(overlay, (center_x, center_y - 15), (center_x, center_y + 15), color, 2)
                
                status_text = f"Status: {self.color_status.upper()}"
                cv2.putText(overlay, status_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            return overlay
            
        except Exception as e:
            logger.error(f"Overlay drawing failed: {str(e)}")
            return img
    
    def _draw_timer_info(self, img: np.ndarray, w: int, h: int):
        try:
            timer_bg = np.zeros((80, w, 3), dtype=np.uint8)
            timer_bg[:] = (0, 0, 0)
            
            if self.is_timer_active():
                remaining = self.get_remaining_time()
                if self.is_capturing_best_frame():
                    capture_remaining = self.get_best_frame_remaining_time()
                    timer_text = f"Timer: {remaining:.1f}s | Capture: {capture_remaining:.1f}s - AUTO CAPTURE!"
                    color = (0, 255, 0)
                elif self.is_check_timer_active():
                    check_remaining = self.get_check_remaining_time()
                    timer_text = f"Timer: {remaining:.1f}s | Check: {check_remaining:.2f}s"
                    color = (0, 255, 0) if check_remaining > 0.4 else (0, 0, 255)
                else:
                    timer_text = f"Timer: {remaining:.1f}s | Check: Waiting for face"
                    color = (0, 255, 255)
            elif self.timer_expired:
                timer_text = "Timer: TIME EXPIRED!"
                color = (0, 0, 255)
            else:
                timer_text = "Timer: Not started"
                color = (128, 128, 128)
            
            cv2.putText(timer_bg, timer_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            status_text = f"Status: {self.color_status.upper()}"
            cv2.putText(timer_bg, status_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            img[:80, :] = timer_bg
            
        except Exception as e:
            logger.error(f"Timer info drawing failed: {str(e)}")
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        return {
            "readiness": self.readiness,
            "ok_frames": self.ok_frames,
            "face_ok": self.face_ok,
            "liveness_ok": self.liveness_ok,
            "mask_suspect": self.mask_suspect,
            "status_text": self.status_text,
            "hint": self.hint,
            "error_text": self.error_text,
            "best_frame": self.best_frame
        }
    
    def is_ready_for_capture(self) -> bool:
        if not self.is_timer_active():
            logger.debug("Not ready: Timer not active")
            return False
        
        conditions = {
            "readiness_ok": self.readiness >= self.readiness_threshold,
            "ok_frames_ok": self.ok_frames >= 1,
            "liveness_ok": self.liveness_ok,
            "no_mask": not self.mask_suspect,
            "face_ok": self.face_ok,
            "has_best_frame": self.best_frame is not None,
            "color_green": self.color_status == "green",
            "status_changed": self.status_changed_to_green,
            "capturing_best_frame": self.is_capturing_best_frame(),
            "capture_completed": not self.is_capturing_best_frame() and self.best_frame is not None
        }
        
        logger.debug(f"Ready conditions: {conditions}")
        logger.debug(f"Readiness: {self.readiness:.3f}, threshold: {self.readiness_threshold:.3f}")
        logger.debug(f"Color status: {self.color_status}, changed to green: {self.status_changed_to_green}")
        logger.debug(f"Capturing best frame: {self.is_capturing_best_frame()}")
        
        result = (self.readiness >= self.readiness_threshold and 
                self.ok_frames >= 1 and
                self.liveness_ok and 
                not self.mask_suspect and 
                self.face_ok and
                self.best_frame is not None and
                self.color_status == "green" and
                self.status_changed_to_green)
        
        if (self.is_capturing_best_frame() and 
            self.best_frame is not None and 
            self.readiness >= 0.6):
            result = True
            logger.info("Early capture allowed - high quality frame detected!")
        
        elif (self.is_capturing_best_frame() and 
              self.readiness >= self.readiness_threshold and
              self.ok_frames >= 1 and
              self.liveness_ok and 
              not self.mask_suspect and 
              self.face_ok and
              self.color_status == "green"):
            result = True
            logger.info("Ready for capture during best frame capture process")
        
        logger.debug(f"Ready for capture: {result}")
        return result
    
    def _reset_timer_for_next_person(self):
        self.timer_start_time = None
        self.timer_expired = False
        self.status_text = "Ready for next person"
        self.hint = "Place face in frame to start"
        self.color_status = "red"
        self.readiness = 0.0
        self.ok_frames = 0
        self.liveness_ok = False
        self.mask_suspect = False
        self.face_ok = False
        self.best_frame = None
        self.capturing_best_frame = False
        self.best_frame_start_time = None
        self.status_changed_to_green = False
        self.timer_reset_time = None
        logger.info("Timer reset for next person")