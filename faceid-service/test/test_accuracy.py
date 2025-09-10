import requests
import os

def test_accuracy():
    """Test model accuracy with known image pairs"""
    print("Accuracy Test - Face Recognition API")
    print("=" * 40)

    test_folder = "test_images"
    images = [f for f in os.listdir(test_folder)
              if f.lower().endswith(('.png', '.jpg', '.jpeg')) 
              and 'no_face' not in f.lower()]

    if len(images) < 2:
        print("ERROR: Need at least 2 valid person images for testing")
        return 0

    print(f"Images found: {len(images)}")

    # --- Test 1: Self-comparison (should match) ---
    print("\n[TEST 1] Self-comparison")
    same_person_results = []
    same_person_similarities = []

    try:
        img_path = os.path.join(test_folder, images[0])
        response = requests.post("http://localhost:5000/encode-face",
                                 files={'image': open(img_path, 'rb')}, timeout=30)

        if response.status_code == 200:
            embedding = response.json()["embedding"]

            compare_response = requests.post("http://localhost:5000/compare-faces", json={
                "embedding1": embedding,
                "embedding2": embedding
            }, timeout=20)

            if compare_response.status_code == 200:
                result = compare_response.json()
                test_pass = result["match"] is True
                same_person_results.append(test_pass)
                same_person_similarities.append(result["similarity"])
                print(f"Match={result['match']}, Similarity={result['similarity']:.3f}")
            else:
                print(f"Compare failed - HTTP {compare_response.status_code}")
        else:
            print(f"Encode failed - HTTP {response.status_code}")

    except Exception as e:
        print(f"ERROR: Self-comparison test failed - {str(e)}")

    # --- Test 2: Cross-comparison (should not match) ---
    print("\n[TEST 2] Cross-comparison")
    different_people_results = []
    different_people_similarities = []

    try:
        img1_path = os.path.join(test_folder, images[0])
        img2_path = os.path.join(test_folder, images[1])

        response1 = requests.post("http://localhost:5000/encode-face",
                                  files={'image': open(img1_path, 'rb')}, timeout=30)
        response2 = requests.post("http://localhost:5000/encode-face",
                                  files={'image': open(img2_path, 'rb')}, timeout=30)

        if response1.status_code == 200 and response2.status_code == 200:
            embedding1 = response1.json()["embedding"]
            embedding2 = response2.json()["embedding"]

            compare_response = requests.post("http://localhost:5000/compare-faces", json={
                "embedding1": embedding1,
                "embedding2": embedding2
            }, timeout=20)

            if compare_response.status_code == 200:
                result = compare_response.json()
                test_pass = result["match"] is False
                different_people_results.append(test_pass)
                different_people_similarities.append(result["similarity"])
                print(f"Match={result['match']}, Similarity={result['similarity']:.3f}")
            else:
                print(f"Compare failed - HTTP {compare_response.status_code}")
        else:
            print(f"Encode failed - Image1={response1.status_code}, Image2={response2.status_code}")

    except Exception as e:
        print(f"ERROR: Cross-comparison test failed - {str(e)}")

    # --- Report ---
    total_tests = len(same_person_results) + len(different_people_results)
    if total_tests == 0:
        print("\nNo tests completed successfully")
        return 0

    correct_tests = sum(same_person_results) + sum(different_people_results)
    accuracy = (correct_tests / total_tests) * 100

    print("\n" + "=" * 40)
    print("ACCURACY REPORT")
    print("=" * 40)
    print(f"Tests completed: {total_tests}")
    print(f"Tests passed: {correct_tests}")
    print(f"Accuracy: {accuracy:.1f}%")

    if same_person_similarities:
        print(f"Self-similarity: {same_person_similarities[0]:.3f}")

    if different_people_similarities:
        print(f"Cross-similarity: {different_people_similarities[0]:.3f}")

    # Threshold analysis
    print("\nThreshold Analysis (0.6)")
    if same_person_similarities and different_people_similarities:
        same_above = same_person_similarities[0] > 0.6
        diff_below = different_people_similarities[0] < 0.6

        print(f"Self-comparison > 0.6: {same_above}")
        print(f"Cross-comparison < 0.6: {diff_below}")

        if same_above and diff_below:
            print(" status: good  ")
        else:
            print(" status: poor needs improve")

    # Final assessment
    print("\n" + "=" * 40)
    if accuracy == 100:
        print("eXCELLENT")
    elif accuracy >= 80:
        print("GOOD")
    else:
        print("LOW")

    return accuracy


if __name__ == "__main__":
    test_accuracy()
