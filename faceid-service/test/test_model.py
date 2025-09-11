import requests
import os
import time
import sys
from typing import List, Optional, Tuple, Dict

class FaceIDTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        print(f"Initializing tester with base URL: {base_url}")
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            print("Testing health check...")
            response = requests.get(f"{self.base_url}/health", timeout=10)
            print(f"Health check response: {response.status_code}")
            if response.status_code == 200:
                result = response.json().get("status") == "healthy"
                self.test_results.append(("Health Check", result, "Service status checked"))
                return result
            else:
                self.test_results.append(("Health Check", False, f"HTTP {response.status_code}"))
                return False
        except Exception as e:
            print(f"Health check error: {str(e)}")
            self.test_results.append(("Health Check", False, str(e)))
            return False
    
    def test_encode_face(self, image_path: str, expected_success: bool = True) -> Optional[str]:
        """Test encoding a face with expected outcome"""
        test_name = f"Encode: {os.path.basename(image_path)}"
        if not expected_success:
            test_name += " (expected fail)"
        
        print(f"Testing: {test_name}")
        
        try:
            if not os.path.exists(image_path):
                self.test_results.append((test_name, False, f"File not found: {image_path}"))
                return None
            
            with open(image_path, 'rb') as f:
                response = requests.post(f"{self.base_url}/encode-face", 
                                       files={'image': f}, timeout=30)
            
            print(f"Encode response: {response.status_code}")
            
            if response.status_code == 200:
                success = "embedding" in response.json()
                if expected_success:
                    result = success
                    details = "Success" if success else "No embedding in response"
                else:
                    result = False  # Should have failed but succeeded
                    details = "Unexpected success"
            else:
                success = False
                if expected_success:
                    result = False  # Should have succeeded but failed
                    error_msg = response.json().get('message', 'Unknown error')
                    details = f"Failed: {error_msg}"
                else:
                    result = True  # Expected to fail and it did
                    error_code = response.json().get('error', '')
                    details = f"Properly rejected: {error_code}"
            
            self.test_results.append((test_name, result, details))
            
            return response.json().get("embedding") if success else None
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"Exception in {test_name}: {error_msg}")
            self.test_results.append((test_name, False, error_msg))
            return None
    
    def test_compare_faces(self, embedding1: str, embedding2: str, expected_match: bool) -> bool:
        """Test face comparison with expected outcome"""
        try:
            print("Testing face comparison...")
            response = requests.post(f"{self.base_url}/compare-faces", json={
                "embedding1": embedding1,
                "embedding2": embedding2
            }, timeout=20)
            
            print(f"Compare response: {response.status_code}")
            
            if response.status_code == 200:
                result_data = response.json()
                match = result_data.get("match", False)
                similarity = result_data.get("similarity", 0)
                
                result = (match == expected_match)
                details = f"Match: {match} (expected: {expected_match}), Similarity: {similarity:.3f}"
                
                self.test_results.append(("Face Comparison", result, details))
                return result
            else:
                error_msg = response.json().get('message', 'Unknown error')
                self.test_results.append(("Face Comparison", False, f"HTTP {response.status_code}: {error_msg}"))
                return False
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"Exception in face comparison: {error_msg}")
            self.test_results.append(("Face Comparison", False, error_msg))
            return False
    
    def run_comprehensive_test(self, test_images_folder: str):
        """Run comprehensive test suite"""
        print("=" * 60)
        print("Running Comprehensive FaceID Test")
        print("=" * 60)
        
        # First check if service is running
        if not self.test_health_check():
            print("Health check failed. Please start the service with: python app.py")
            return False
        
        if not os.path.exists(test_images_folder):
            print(f"Test folder '{test_images_folder}' not found")
            return False
        
        images = [f for f in os.listdir(test_images_folder) 
                 if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not images:
            print("No test images found")
            return False
        
        print(f"Found {len(images)} test images: {', '.join(images)}")
        
        # Categorize images
        person_images = []
        mask_images = []
        no_face_images = []
        
        for img in images:
            img_lower = img.lower()
            if 'mask' in img_lower:
                mask_images.append(img)
            elif 'no_face' in img_lower:
                no_face_images.append(img)
            else:
                person_images.append(img)
        
        print(f"Person images: {len(person_images)}")
        print(f"Mask images: {len(mask_images)}")
        print(f"No-face images: {len(no_face_images)}")
        
        # Test mask images (should fail)
        for mask_img in mask_images:
            img_path = os.path.join(test_images_folder, mask_img)
            self.test_encode_face(img_path, expected_success=False)
        
        # Test no-face images (should fail)
        for no_face_img in no_face_images:
            img_path = os.path.join(test_images_folder, no_face_img)
            self.test_encode_face(img_path, expected_success=False)
        
        # Test person images (should succeed)
        embeddings = []
        for person_img in person_images:
            img_path = os.path.join(test_images_folder, person_img)
            embedding = self.test_encode_face(img_path, expected_success=True)
            if embedding:
                embeddings.append((person_img, embedding))
        
        # Test comparisons
        if len(embeddings) >= 1:
            img1, emb1 = embeddings[0]
            # Self-comparison
            self.test_compare_faces(emb1, emb1, expected_match=True)
        
        if len(embeddings) >= 2:
            img1, emb1 = embeddings[0]
            img2, emb2 = embeddings[1]
            # Cross-comparison
            self.test_compare_faces(emb1, emb2, expected_match=False)
        
        self.print_results()
        return self.calculate_success()
    
    def print_results(self):
        """Print formatted test results"""
        print("\n" + "=" * 60)
        print("Test Results")
        print("=" * 60)
        
        for test_name, result, details in self.test_results:
            status = "PASS" if result else "FAIL"
            print(f"{status} {test_name}")
            print(f"   {details}")
            print()
    
    def calculate_success(self) -> bool:
        """Calculate overall test success"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, result, _ in self.test_results if result)
        
        if total_tests == 0:
            print("No tests completed")
            return False
        
        accuracy = (passed_tests / total_tests) * 100
        
        print("=" * 60)
        print(f"SUMMARY: {passed_tests}/{total_tests} tests passed ({accuracy:.1f}%)")
        
        if accuracy == 100:
            print("ALL TESTS PASSED!")
            return True
        elif accuracy >= 80:
            print("GOOD - Most tests passed")
            return True
        elif accuracy >= 60:
            print("FAIR - Some tests failed")
            return False
        else:
            print("POOR - Many tests failed")
            return False

# Run the test
if __name__ == "__main__":
    # Check if service is running first
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("Service is running")
        else:
            print("Service returned error status")
    except:
        print("Service is not running. Please start it with: python app.py")
        sys.exit(1)
    
    tester = FaceIDTester()
    
    test_folder = "test_images"
    if not os.path.exists(test_folder):
        print(f"Test folder '{test_folder}' not found")
        sys.exit(1)
    
    success = tester.run_comprehensive_test(test_folder)
    sys.exit(0 if success else 1)