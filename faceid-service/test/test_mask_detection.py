import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from PIL import Image
import requests
import json
from typing import Dict, List, Tuple
import time

class MaskDetectionTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = []
    
    def test_individual_images(self, test_folder: str):
        """Test từng ảnh riêng biệt và phân tích kết quả"""
        print("Testing Mask Detection on Individual Images")
        print("=" * 60)
        
        if not os.path.exists(test_folder):
            print(f"Test folder '{test_folder}' not found")
            return
        
        images = [f for f in os.listdir(test_folder) 
                 if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not images:
            print("No test images found")
            return
        
        print(f"Found {len(images)} images")
        print()
        
        for img_name in sorted(images):
            img_path = os.path.join(test_folder, img_name)
            self._test_single_image(img_path, img_name)
        
        self._print_summary()
    
    def _test_single_image(self, img_path: str, img_name: str):
        print(f"Testing: {img_name}")
        print("-" * 40)
        
        try:
            # Gửi request đến API
            start_time = time.time()
            with open(img_path, 'rb') as f:
                response = requests.post(f"{self.base_url}/encode-face", 
                                       files={'image': f}, timeout=30)
            processing_time = (time.time() - start_time) * 1000
            
            # Phân tích response
            if response.status_code == 200:
                # Thành công - không có mask
                result = {
                    'image': img_name,
                    'status': 'success',
                    'mask_detected': False,
                    'confidence': 0.0,
                    'processing_time': processing_time,
                    'expected_mask': 'mask' in img_name.lower(),
                    'correct': 'mask' not in img_name.lower()
                }
                print(f"No mask detected")
                print(f" Time: {processing_time:.2f}ms")
                
            elif response.status_code == 400:
                # Lỗi - phân tích loại lỗi
                error_data = response.json()
                error_code = error_data.get('error', '')
                error_msg = error_data.get('message', '')
                
                mask_detected = error_code == 'FACE_MASK_DETECTED'
                confidence = self._extract_confidence(error_msg)
                
                result = {
                    'image': img_name,
                    'status': 'error',
                    'error_code': error_code,
                    'mask_detected': mask_detected,
                    'confidence': confidence,
                    'processing_time': processing_time,
                    'expected_mask': 'mask' in img_name.lower(),
                    'correct': mask_detected == ('mask' in img_name.lower())
                }
                
                if mask_detected:
                    print(f"mask detected: {error_msg}")
                    print(f"Confidence: {confidence:.2f}")
                else:
                    print(f" Other error: {error_code} - {error_msg}")
                
                print(f"Time: {processing_time:.2f}ms")
                
            else:
                # Lỗi khác
                result = {
                    'image': img_name,
                    'status': 'unknown_error',
                    'error_code': f"HTTP_{response.status_code}",
                    'processing_time': processing_time,
                    'correct': False
                }
                print(f"Unexpected status: {response.status_code}")
            
            self.results.append(result)
            
        except Exception as e:
            error_result = {
                'image': img_name,
                'status': 'exception',
                'error': str(e),
                'processing_time': 0,
                'correct': False
            }
            self.results.append(error_result)
            print(f" Exception: {str(e)}")
        
        print()
    
    def _extract_confidence(self, error_msg: str) -> float:
        """Trích xuất confidence từ error message"""
        import re
        match = re.search(r'confidence:?\s*([0-9.]+)', error_msg, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 0.0
    
    def _print_summary(self):
        """In summary chi tiết"""
        print("=" * 60)
        print("MASK DETECTION SUMMARY")
        print("=" * 60)
        
        total = len(self.results)
        correct = sum(1 for r in self.results if r.get('correct', False))
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Phân loại kết quả
        mask_images = [r for r in self.results if 'mask' in r['image'].lower()]
        no_mask_images = [r for r in self.results if 'mask' not in r['image'].lower()]
        
        print(f"Overall Accuracy: {accuracy:.1f}% ({correct}/{total})")
        print()
        
        # Mask images analysis
        print("MASK IMAGES (should be detected):")
        for result in mask_images:
            status = "✅" if result.get('correct') else "❌"
            confidence = result.get('confidence', 0)
            print(f"   {status} {result['image']}: {result.get('error_code', 'N/A')} "
                  f"(conf: {confidence:.2f})")
        
        print()
        
        # No mask images analysis  
        print("NO MASK IMAGES (should NOT be detected):")
        for result in no_mask_images:
            status = "✅" if result.get('correct') else "❌"
            print(f"   {status} {result['image']}: {result.get('status', 'N/A')}")
        
        print()
        
        # Confidence analysis
        mask_confidences = [r.get('confidence', 0) for r in self.results 
                          if r.get('mask_detected', False)]
        if mask_confidences:
            print("Confidence Statistics for Detected Masks:")
            print(f"   Average: {np.mean(mask_confidences):.2f}")
            print(f"   Min: {min(mask_confidences):.2f}")
            print(f"   Max: {max(mask_confidences):.2f}")
        
        # Performance analysis
        processing_times = [r.get('processing_time', 0) for r in self.results]
        print(f"⏱️  Average Processing Time: {np.mean(processing_times):.2f}ms")
        
        print()
        print("=" * 60)
        
        if accuracy == 100:
            print("EXCELLENT - Perfect mask detection!")
        elif accuracy >= 80:
            print("GOOD - Reliable mask detection")
        elif accuracy >= 60:
            print("FAIR - Needs improvement")
        else:
            print("POOR - Mask detection not working properly")
    
    def visualize_results(self, test_folder: str):
        """Visualize kết quả với ảnh (cần matplotlib)"""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print(" matplotlib not installed. Skipping visualization.")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, result in enumerate(self.results[:6]):
            img_path = os.path.join(test_folder, result['image'])
            if os.path.exists(img_path):
                img = cv2.imread(img_path)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                axes[i].imshow(img_rgb)
                
                # Title với kết quả
                status = "✅" if result.get('correct') else "❌"
                mask_status = "MASK" if result.get('mask_detected') else "NO MASK"
                title = f"{status} {result['image']}\n{mask_status}"
                if result.get('confidence', 0) > 0:
                    title += f"\nconf: {result['confidence']:.2f}"
                
                axes[i].set_title(title, fontsize=10)
                axes[i].axis('off')
        
        plt.tight_layout()
        plt.savefig('mask_detection_results.png')
        print("📸 Visualization saved as 'mask_detection_results.png'")
    
    def generate_report(self):
        """Tạo báo cáo chi tiết"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results if r.get('correct', False)),
            "accuracy": (sum(1 for r in self.results if r.get('correct', False)) / len(self.results) * 100) 
                       if self.results else 0,
            "details": self.results
        }
        
        with open('mask_detection_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("📄 Report saved as 'mask_detection_report.json'")

def test_mask_detection_threshold():
    """Test các threshold khác nhau để tìm optimal value"""
    print("🎚️ Testing Different Threshold Values")
    print("=" * 50)
    
    # Test image với mask
    test_image = "test_images/person1_with_mask.png"
    
    if not os.path.exists(test_image):
        print("❌ Mask test image not found")
        return
    
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    print("Threshold | Detection | Confidence | Result")
    print("-" * 45)
    
    for threshold in thresholds:
        try:
            # Gửi request và check response
            with open(test_image, 'rb') as f:
                response = requests.post(f"{self.base_url}/encode-face", 
                                       files={'image': f}, timeout=30)
            
            detected = response.status_code == 400
            confidence = 0.0
            
            if detected:
                error_msg = response.json().get('message', '')
                confidence = float(''.join(filter(lambda x: x.isdigit() or x == '.', error_msg.split('confidence:')[-1].split()[0])))
            
            result = "✅" if detected else "❌"
            print(f"   {threshold:.1f}    |   {detected}   |   {confidence:.2f}   |  {result}")
            
        except Exception as e:
            print(f"   {threshold:.1f}    |   ERROR    |   N/A     |  ❌")
    
    print()
    print("💡 Recommendation: Choose threshold where mask is detected with high confidence")

if __name__ == "__main__":
    # Kiểm tra service
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Service not running. Please start with: python app.py")
            exit(1)
    except:
        print("❌ Service not running. Please start with: python app.py")
        exit(1)
    
    # Chạy test
    tester = MaskDetectionTester()
    
    print("🚀 Starting Comprehensive Mask Detection Test")
    print()
    
    # Test tất cả ảnh
    tester.test_individual_images("test_images")
    
    # Visualize results
    tester.visualize_results("test_images")
    
    # Generate report
    tester.generate_report()
    
    # Test thresholds
    test_mask_detection_threshold()