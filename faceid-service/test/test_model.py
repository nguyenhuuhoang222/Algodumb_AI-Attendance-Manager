import requests
import os
import time
from typing import List, Optional

class FaceIDTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
    
    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            result = response.status_code == 200 and response.json()["status"] == "healthy"
            self.test_results.append(("Health Check", result, "Service status checked"))
            return result
        except Exception as e:
            self.test_results.append(("Health Check", False, str(e)))
            return False
    
    def test_encode_face(self, image_path: str, should_succeed: bool = True) -> Optional[str]:
        """Test encoding a face with expected outcome"""
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(f"{self.base_url}/encode-face", files=files, timeout=30)
            
            success = response.status_code == 200 and "embedding" in response.json()
            
           
            result = (success == should_succeed)
            
            test_name = f"Encode Face: {os.path.basename(image_path)}"
            if not should_succeed:
                test_name += " (no face expected)"
            
            details = "Success" if success else "No face detected - expected" if not should_succeed else "Unexpected failure"
            self.test_results.append((test_name, result, details))
            
            return response.json().get("embedding") if success else None
            
        except Exception as e:
            error_msg = f"Error: {str(e)}" 
            if "No faces detected" in str(e) and not should_succeed:
                # This is actually a PASS for no-face images
                self.test_results.append((f"Encode Face: {os.path.basename(image_path)} (no face expected)", True, "Correctly detected no face"))
                return None
            else:
                self.test_results.append((f"Encode Face: {os.path.basename(image_path)}", False, error_msg))
                return None
    
    def test_compare_faces(self, embedding1: str, embedding2: str, expected_match: bool) -> bool:
        """Test face comparison with expected outcome"""
        try:
            response = requests.post(f"{self.base_url}/compare-faces", json={
                "embedding1": embedding1,
                "embedding2": embedding2
            }, timeout=20)
            
            if response.status_code == 200:
                match = response.json()["match"]
                similarity = response.json().get("similarity", 0)
                result = (match == expected_match)
                
                details = f"Match: {match}, Similarity: {similarity:.3f}, Expected: {expected_match}"
                self.test_results.append((f"Face Comparison", result, details))
                return result
            return False
            
        except Exception as e:
            self.test_results.append((f"Face Comparison", False, str(e)))
            return False
    
    def run_optimized_test(self, test_images_folder: str):
        """Run optimized test suite without duplicates"""
        print("Running FaceID Model Test")
        print("-" * 50)
        
        if not self.test_health_check():
            print("Health check failed, service not running.")
            return False
        
        all_images = [f for f in os.listdir(test_images_folder) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        unique_images = list(dict.fromkeys(all_images))
        
        if len(unique_images) < 2:
            print("Not enough images for testing (need >= 2).")
            return False
        
        print(f"Found {len(unique_images)} test images")
        
        person_images, no_face_images = [], []
        
        for img_file in unique_images:
            img_path = os.path.join(test_images_folder, img_file)
            
            if 'no_face' in img_file.lower():
                self.test_encode_face(img_path, should_succeed=False)
                no_face_images.append(img_file)
            else:
                embedding = self.test_encode_face(img_path, should_succeed=True)
                if embedding:
                    person_images.append((img_file, embedding))
        
        if len(person_images) >= 1:
            img1, emb1 = person_images[0]
            self.test_compare_faces(emb1, emb1, expected_match=True)
        
        if len(person_images) >= 2:
            img1, emb1 = person_images[0]
            img2, emb2 = person_images[1]
            self.test_compare_faces(emb1, emb2, expected_match=False)
        
        self.print_results()
        return self.calculate_success()
    
    def print_results(self):
        """Print formatted test results"""
        print("\nTest Results")
        print("-" * 50)
        for test_name, result, details in self.test_results:
            status = "PASS" if result else "FAIL"
            print(f"[{status}] {test_name} - {details}")
    
    def calculate_success(self) -> bool:
        """Calculate overall test success"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, result, _ in self.test_results if result)
        accuracy = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("-" * 50)
        print(f"Summary: {passed_tests}/{total_tests} passed ({accuracy:.1f}%)")
        
        if accuracy == 100:
            print("All tests passed.")
        elif accuracy >= 80:
            print("Most tests passed.")
        else:
            print("Many tests failed.")
        
        return accuracy == 100


# Run the optimized test
if __name__ == "__main__":
    tester = FaceIDTester()
    
    test_folder = "test_images"
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)
        print(f"Created {test_folder} folder. Please add test images.")
    else:
        success = tester.run_optimized_test(test_folder)