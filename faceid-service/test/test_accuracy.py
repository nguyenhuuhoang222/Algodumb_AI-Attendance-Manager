import requests
import os
import base64
from typing import Dict, List, Tuple

def test_accuracy():
    """
    🎯 KIỂM TRA ĐỘ CHÍNH XÁC HỆ THỐNG NHẬN DIỆN KHUÔN MẶT
    
    Function này test 4 khả năng quan trọng:
    1. So sánh cùng 1 người (phải nhận ra là giống)
    2. So sánh 2 người khác nhau (phải nhận ra là khác)  
    3. Phát hiện ảnh đeo khẩu trang (phải từ chối)
    4. Phát hiện ảnh không có mặt người (phải từ chối)
    """
    print("🎯 Accuracy Test - Face Recognition API")
    print("=" * 60)
    print("📁 Test Images Analysis:")
    print("=" * 60)

    test_folder = "test_images"
    if not os.path.exists(test_folder):
        print(f"❌ ERROR: Test folder '{test_folder}' not found")
        return 0

    images = [f for f in os.listdir(test_folder)
              if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if len(images) < 2:
        print("❌ ERROR: Need at least 2 images for testing")
        return 0

    print(f"📊 Images found: {len(images)}")
    
    # Phân loại ảnh thành 3 nhóm
    person_images = []    # Ảnh người bình thường
    mask_images = []      # Ảnh đeo khẩu trang  
    no_face_images = []   # Ảnh không có mặt người
    
    for img in images:
        if 'mask' in img.lower():
            mask_images.append(img)
            print(f"   😷 Mask image: {img}")
        elif 'no_face' in img.lower():
            no_face_images.append(img)
            print(f"   🚫 No-face image: {img}")
        else:
            person_images.append(img)
            print(f"   👤 Person image: {img}")
    
    print(f"\n📈 Summary: {len(person_images)} persons, {len(mask_images)} masks, {len(no_face_images)} no-face")
    print("=" * 60)

    test_results = []    # Lưu kết quả các test
    similarities = []    # Lưu điểm similarity

    # --- TEST 1: So sánh cùng 1 người ---
    if len(person_images) >= 1:
        print("\n[TEST 1] 🔄 Self-comparison (same person)")
        print("-" * 40)
        result = test_self_comparison(test_folder, person_images[0])
        test_results.append(("Self-comparison", result["passed"], result["similarity"]))
        similarities.append(("Self", result["similarity"]))

    # --- TEST 2: So sánh 2 người khác nhau ---
    if len(person_images) >= 2:
        print("\n[TEST 2] 🔄 Cross-comparison (different persons)")
        print("-" * 40)
        result = test_cross_comparison(test_folder, person_images[0], person_images[1])
        test_results.append(("Cross-comparison", result["passed"], result["similarity"]))
        similarities.append(("Cross", result["similarity"]))

    # --- TEST 3: Phát hiện khẩu trang ---
    if mask_images:
        print("\n[TEST 3] 😷 Mask detection (should reject)")
        print("-" * 40)
        result = test_mask_detection(test_folder, mask_images[0])
        test_results.append(("Mask detection", result["passed"], 0))
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"  {status} - {result['message']}")

    # --- TEST 4: Phát hiện không có mặt ---
    if no_face_images:
        print("\n[TEST 4] 🚫 No face detection (should reject)")
        print("-" * 40)
        result = test_no_face_detection(test_folder, no_face_images[0])
        test_results.append(("No face detection", result["passed"], 0))
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"  {status} - {result['message']}")

    # --- BÁO CÁO KẾT QUẢ ---
    print("\n" + "=" * 60)
    print("📊 ACCURACY REPORT")
    print("=" * 60)
    
    total_tests = len(test_results)
    if total_tests == 0:
        print("❌ No tests completed successfully")
        return 0

    passed_tests = sum(1 for _, passed, _ in test_results if passed)
    accuracy = (passed_tests / total_tests) * 100

    print(f"🧪 Tests completed: {total_tests}")
    print(f"✅ Tests passed: {passed_tests}")
    print(f"🎯 Accuracy: {accuracy:.1f}%")

    # Hiển thị điểm similarity
    if similarities:
        print("\n📈 Similarity Scores:")
        for test_type, similarity in similarities:
            if test_type == "Self":
                print(f"   🔄 Self-comparison: {similarity:.3f} (should be >0.6)")
            else:
                print(f"   🔄 Cross-comparison: {similarity:.3f} (should be <0.6)")

    # Phân tích ngưỡng
    print("\n⚡ Threshold Analysis (0.6):")
    if len(similarities) >= 2:
        self_similarity = next(s for t, s in similarities if t == "Self")
        cross_similarity = next(s for t, s in similarities if t == "Cross")
        
        self_above = self_similarity > 0.6
        cross_below = cross_similarity < 0.6
        
        print(f"   ✅ Self > 0.6: {self_above} ({self_similarity:.3f})")
        print(f"   ✅ Cross < 0.6: {cross_below} ({cross_similarity:.3f})")
        
        if self_above and cross_below:
            print("   🎉 Threshold status: EXCELLENT")
        else:
            print("   ⚠️  Threshold status: NEEDS ADJUSTMENT")

    # Đánh giá cuối cùng
    print("\n" + "=" * 60)
    if accuracy == 100:
        print("🎉 EXCELLENT - All tests passed!")
    elif accuracy >= 80:
        print("👍 GOOD - Most tests passed")
    elif accuracy >= 60:
        print("⚠️  FAIR - Some tests failed")
    else:
        print("❌ POOR - Many tests failed")

    return accuracy

def test_self_comparison(test_folder: str, image_name: str) -> Dict:
    """
    🔄 TEST SO SÁNH CÙNG 1 NGƯỜI
    So sánh 1 ảnh với chính nó - phải trả về kết quả GIỐNG NHAU
    """
    try:
        img_path = os.path.join(test_folder, image_name)
        
        print(f"  🔄 Comparing: {image_name} vs {image_name} (same image)")
        print(f"  📝 Expected: MUST MATCH (same person)")
        
        # Mã hóa khuôn mặt
        with open(img_path, 'rb') as f:
            response = requests.post("http://localhost:5000/encode-face",
                                    files={'image': f}, timeout=30)

        if response.status_code != 200:
            error_msg = f"Encode failed: {response.status_code}"
            if response.status_code == 400:
                error_data = response.json()
                error_msg = f"{error_data.get('error', 'Unknown error')}: {error_data.get('message', 'No message')}"
            return {"passed": False, "similarity": 0, "message": error_msg}

        embedding = response.json()["embedding"]

        # So sánh với chính nó
        compare_response = requests.post("http://localhost:5000/compare-faces", json={
            "embedding1": embedding,
            "embedding2": embedding
        }, timeout=20)

        if compare_response.status_code != 200:
            error_msg = f"Compare failed: {compare_response.status_code}"
            if compare_response.status_code == 400:
                error_data = compare_response.json()
                error_msg = f"{error_data.get('error', 'Unknown error')}: {error_data.get('message', 'No message')}"
            return {"passed": False, "similarity": 0, "message": error_msg}

        result = compare_response.json()
        passed = result.get("match", False) is True
        similarity = result.get("similarity", 0)
        
        print(f"  ✅ Result: Match={result['match']}, Similarity={similarity:.3f}")
        
        return {"passed": passed, "similarity": similarity, "message": "Self-comparison completed"}

    except Exception as e:
        return {"passed": False, "similarity": 0, "message": f"Error: {str(e)}"}

def test_cross_comparison(test_folder: str, image1: str, image2: str) -> Dict:
    """
    🔄 TEST SO SÁNH 2 NGƯỜI KHÁC NHAU  
    So sánh 2 ảnh của 2 người khác nhau - phải trả về kết quả KHÁC NHAU
    """
    try:
        img1_path = os.path.join(test_folder, image1)
        img2_path = os.path.join(test_folder, image2)

        print(f"  🔄 Comparing: {image1} vs {image2} (different persons)")
        print(f"  📝 Expected: MUST NOT MATCH (different persons)")

        # Mã hóa khuôn mặt thứ nhất
        with open(img1_path, 'rb') as f:
            response1 = requests.post("http://localhost:5000/encode-face",
                                     files={'image': f}, timeout=30)
        if response1.status_code != 200:
            error_msg = f"Encode image1 failed: {response1.status_code}"
            if response1.status_code == 400:
                error_data = response1.json()
                error_msg = f"{error_data.get('error', 'Unknown error')}: {error_data.get('message', 'No message')}"
            return {"passed": False, "similarity": 0, "message": error_msg}

        # Mã hóa khuôn mặt thứ hai
        with open(img2_path, 'rb') as f:
            response2 = requests.post("http://localhost:5000/encode-face",
                                     files={'image': f}, timeout=30)
        if response2.status_code != 200:
            error_msg = f"Encode image2 failed: {response2.status_code}"
            if response2.status_code == 400:
                error_data = response2.json()
                error_msg = f"{error_data.get('error', 'Unknown error')}: {error_data.get('message', 'No message')}"
            return {"passed": False, "similarity": 0, "message": error_msg}

        embedding1 = response1.json()["embedding"]
        embedding2 = response2.json()["embedding"]

        # So sánh 2 khuôn mặt
        compare_response = requests.post("http://localhost:5000/compare-faces", json={
            "embedding1": embedding1,
            "embedding2": embedding2
        }, timeout=20)

        if compare_response.status_code != 200:
            error_msg = f"Compare failed: {compare_response.status_code}"
            if compare_response.status_code == 400:
                error_data = compare_response.json()
                error_msg = f"{error_data.get('error', 'Unknown error')}: {error_data.get('message', 'No message')}"
            return {"passed": False, "similarity": 0, "message": error_msg}

        result = compare_response.json()
        passed = result.get("match", True) is False  # Should NOT match
        similarity = result.get("similarity", 0)
        
        print(f"  ✅ Result: Match={result['match']}, Similarity={similarity:.3f}")
        
        return {"passed": passed, "similarity": similarity, "message": "Cross-comparison completed"}

    except Exception as e:
        return {"passed": False, "similarity": 0, "message": f"Error: {str(e)}"}

def test_mask_detection(test_folder: str, image_name: str) -> Dict:
    """
    😷 TEST PHÁT HIỆN KHẨU TRANG
    Kiểm tra hệ thống có từ chối ảnh đeo khẩu trang không
    """
    try:
        img_path = os.path.join(test_folder, image_name)
        
        print(f"  😷 Testing mask detection on: {image_name}")
        print(f"  📝 Expected: MUST REJECT (mask detected)")
        
        with open(img_path, 'rb') as f:
            response = requests.post("http://localhost:5000/encode-face",
                                    files={'image': f}, timeout=30)

        # Phải trả về lỗi 400 và mã lỗi FACE_MASK_DETECTED
        passed = (response.status_code == 400 and 
                 response.json().get("error") == "FACE_MASK_DETECTED")
        
        message = response.json().get("message", "Unknown error") if response.status_code != 200 else "Unexpected success"
        
        return {"passed": passed, "message": message}

    except Exception as e:
        return {"passed": False, "message": f"Error: {str(e)}"}

def test_no_face_detection(test_folder: str, image_name: str) -> Dict:
    """
    🚫 TEST PHÁT HIỆN KHÔNG CÓ MẶT
    Kiểm tra hệ thống có từ chối ảnh không có khuôn mặt không
    """
    try:
        img_path = os.path.join(test_folder, image_name)
        
        print(f"  🚫 Testing no-face detection on: {image_name}")
        print(f"  📝 Expected: MUST REJECT (no face detected)")
        
        with open(img_path, 'rb') as f:
            response = requests.post("http://localhost:5000/encode-face",
                                    files={'image': f}, timeout=30)

        # Phải trả về lỗi 400 và mã lỗi về không có mặt
        passed = (response.status_code == 400 and 
                 response.json().get("error") in ["NO_FACE_DETECTED", "IMAGE_PROCESSING_ERROR"])
        
        message = response.json().get("message", "Unknown error") if response.status_code != 200 else "Unexpected success"
        
        return {"passed": passed, "message": message}

    except Exception as e:
        return {"passed": False, "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    test_accuracy()