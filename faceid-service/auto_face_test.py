import cv2
import numpy as np
import time
import os
import json
from deepface import DeepFace
import insightface
from insightface.app import FaceAnalysis
from PIL import Image
import base64

class AutoFaceTester:
    def __init__(self):
        """Initialize face recognition and anti-spoofing models"""
        print("Initializing models...")
        
        # Initialize InsightFace
        self.face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        
        # Load reference image (person1)
        self.reference_image_path = "test/test_images/person1.jpg"
        self.reference_embedding = self._get_reference_embedding()
        
        # Test states
        self.test_state = "detecting_face"
        self.face_detected = False
        self.mask_detected = False
        self.spoof_detected = False
        self.verification_passed = False
        
        # Results storage
        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "details": []
        }
    
    def _get_reference_embedding(self):
        """Get embedding from reference image"""
        try:
            if not os.path.exists(self.reference_image_path):
                print(f"Reference image not found: {self.reference_image_path}")
                return None
            
            img = cv2.imread(self.reference_image_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = self.face_app.get(img_rgb)
            
            if len(faces) == 0:
                print("No face found in reference image")
                return None
            
            return faces[0].embedding
            
        except Exception as e:
            print(f"Error loading reference image: {e}")
            return None
    
    def _check_mask(self, face_region):
        """Check if face has mask using basic heuristics"""
        try:
            if face_region.size == 0:
                return False, 0.0
            
            height, width = face_region.shape[:2]
            
            # Only check lower part of face for masks
            lower_face = face_region[int(height*0.6):, :]
            
            if lower_face.size == 0:
                return False, 0.0
            
            # Convert to different color spaces
            gray_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2GRAY)
            hsv_lower = cv2.cvtColor(lower_face, cv2.COLOR_BGR2HSV)
            
            # Calculate multiple features
            features = []
            
            # 1. Color variance (masks often have uniform color)
            color_variance = np.var(lower_face)
            features.append(min(color_variance / 500, 1.0))
            
            # 2. Texture analysis
            texture_var = cv2.Laplacian(gray_lower, cv2.CV_64F).var()
            features.append(min((100 - texture_var) / 100, 1.0))
            
            # 3. Saturation analysis (masks often have low saturation)
            saturation_mean = np.mean(hsv_lower[:,:,1])
            features.append(min((50 - saturation_mean) / 50, 1.0))
            
            # 4. Edge density
            edges = cv2.Canny(gray_lower, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size
            features.append(min((0.1 - edge_density) / 0.1, 1.0))
            
            # Weighted average
            weights = [0.2, 0.4, 0.2, 0.2]
            mask_confidence = sum(w * f for w, f in zip(weights, features))
            
            return mask_confidence > 0.7, float(mask_confidence)
            
        except Exception as e:
            print(f"Mask check error: {e}")
            return False, 0.0
    
    def _check_spoof(self, face_region):
        """Check if face is real or spoofed using DeepFace"""
        try:
            if face_region.size == 0:
                return True, 0.5
            
            # Convert to RGB for DeepFace
            face_rgb = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
            
            # Use DeepFace for spoof detection
            result = DeepFace.analyze(
                img_path=face_rgb,
                actions=['spoof'],
                detector_backend='skip',
                enforce_detection=False,
                silent=True
            )
            
            # Extract spoof score (0=real, 1=spoof)
            if isinstance(result, list):
                spoof_score = result[0]['spoof']
            else:
                spoof_score = result['spoof']
            
            # Convert to real confidence
            real_confidence = 1.0 - spoof_score
            is_real = real_confidence > 0.7
            
            return is_real, float(real_confidence)
            
        except Exception as e:
            print(f"Spoof check error: {e}")
            return True, 0.5
    
    def _verify_face(self, embedding):
        """Verify if face matches reference person"""
        try:
            if self.reference_embedding is None:
                return False, 0.0
            
            # Normalize embeddings
            ref_norm = self.reference_embedding / np.linalg.norm(self.reference_embedding)
            test_norm = embedding / np.linalg.norm(embedding)
            
            # Calculate cosine similarity
            similarity = np.dot(ref_norm, test_norm)
            
            return similarity > 0.6, float(similarity)
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False, 0.0
    
    def run_test(self):
        """Run automatic face test with camera"""
        print("Starting automatic face test...")
        print("Press 'q' to quit, 'c' to capture manually")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Cannot open camera")
            return
        
        test_count = 0
        max_tests = 5
        
        while test_count < max_tests:
            ret, frame = cap.read()
            if not ret:
                print("Error: Cannot read frame")
                break
            
            # Display current state
            display_frame = frame.copy()
            cv2.putText(display_frame, f"State: {self.test_state}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Tests: {test_count}/{max_tests}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Process based on current state
            if self.test_state == "detecting_face":
                result = self._process_detection_state(frame, display_frame)
                if result:
                    test_count += 1
                    time.sleep(2)  # Pause between tests
            
            # Show instructions
            cv2.putText(display_frame, "Press 'q' to quit, 'c' to capture", 
                       (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Auto Face Test', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self._manual_capture(frame)
                test_count += 1
                time.sleep(2)
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Print summary
        self._print_summary()
    
    def _process_detection_state(self, frame, display_frame):
        """Process frame in detection state"""
        try:
            # Convert to RGB for face detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = self.face_app.get(rgb_frame)
            
            if len(faces) == 0:
                cv2.putText(display_frame, "No face detected", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                return False
            
            # Get the first face
            face = faces[0]
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            
            # Draw face bounding box
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Extract face region
            face_region = frame[y1:y2, x1:x2]
            
            # Check mask
            has_mask, mask_conf = self._check_mask(face_region)
            if has_mask:
                cv2.putText(display_frame, f"Mask detected! ({mask_conf:.2f})", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                self.test_state = "mask_detected"
                return False
            
            # Check spoof
            is_real, spoof_conf = self._check_spoof(face_region)
            if not is_real:
                cv2.putText(display_frame, f"Spoof detected! ({spoof_conf:.2f})", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                self.test_state = "spoof_detected"
                return False
            
            # Verify face
            is_match, similarity = self._verify_face(face.embedding)
            
            if is_match:
                cv2.putText(display_frame, f"Verified! ({similarity:.2f})", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                self.test_state = "verified"
                result = True
            else:
                cv2.putText(display_frame, f"Not verified! ({similarity:.2f})", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                self.test_state = "not_verified"
                result = False
            
            # Save test result
            self._save_test_result({
                "timestamp": time.time(),
                "mask_detected": has_mask,
                "mask_confidence": mask_conf,
                "spoof_detected": not is_real,
                "spoof_confidence": spoof_conf,
                "verified": is_match,
                "similarity": similarity,
                "success": is_match
            })
            
            return result
            
        except Exception as e:
            print(f"Processing error: {e}")
            return False
    
    def _manual_capture(self, frame):
        """Manual capture for testing"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = self.face_app.get(rgb_frame)
            
            if len(faces) == 0:
                print("No face found for manual capture")
                return
            
            face = faces[0]
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            face_region = frame[y1:y2, x1:x2]
            
            # Run all checks
            has_mask, mask_conf = self._check_mask(face_region)
            is_real, spoof_conf = self._check_spoof(face_region)
            is_match, similarity = self._verify_face(face.embedding)
            
            # Save result
            self._save_test_result({
                "timestamp": time.time(),
                "mask_detected": has_mask,
                "mask_confidence": mask_conf,
                "spoof_detected": not is_real,
                "spoof_confidence": spoof_conf,
                "verified": is_match,
                "similarity": similarity,
                "success": is_match,
                "manual": True
            })
            
            print(f"Manual capture - Mask: {has_mask}, Spoof: {not is_real}, Verified: {is_match}")
            
        except Exception as e:
            print(f"Manual capture error: {e}")
    
    def _save_test_result(self, result):
        """Save test result to history"""
        self.test_results["total_tests"] += 1
        if result["success"]:
            self.test_results["passed_tests"] += 1
        else:
            self.test_results["failed_tests"] += 1
        
        self.test_results["details"].append(result)
        
        # Save to file
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"Total tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        
        if self.test_results['total_tests'] > 0:
            success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        print(f"Results saved to test_results.json")
        print("="*50)

def main():
    """Main function"""
    print("Auto Face Test Program")
    print("This program will:")
    print("1. Open camera and detect faces")
    print("2. Check for masks")
    print("3. Check for spoofing")
    print("4. Verify against person1 reference")
    print("5. Repeat 5 times automatically")
    
    # Check if reference image exists
    if not os.path.exists("test/test_images/person1.jpg"):
        print("Error: Reference image not found at test_images/person1.jpg")
        print("Please place person1.jpg in the test_images folder")
        return
    
    tester = AutoFaceTester()
    tester.run_test()

if __name__ == "__main__":
    main()