import requests
import time
import statistics

def test_performance():
    """Test API performance metrics"""
    print("Performance Test - FaceID API")
    print("-" * 40)
    
    test_image = "test_images/person1.jpg"
    encode_times = []
    compare_times = []
    
    # Phase 1: Face Encoding Performance
    print("[ENCODE] Running face encoding benchmark...")
    for i in range(3):
        try:
            with open(test_image, 'rb') as f:
                start_time = time.time()
                response = requests.post("http://localhost:5000/encode-face", 
                                         files={'image': f}, timeout=30)
                end_time = time.time()
            
            if response.status_code == 200:
                time_ms = (end_time - start_time) * 1000
                encode_times.append(time_ms)
                print(f"Run {i+1}: {time_ms:.2f} ms")
            else:
                print(f"Run {i+1}: FAILED ({response.status_code})")
                
        except Exception as e:
            print(f"Run {i+1}: ERROR - {str(e)}")
            return False
    
    # Phase 2: Get embedding for comparison tests
    print("\n[COMPARE] Preparing embedding...")
    embedding = None
    try:
        with open(test_image, 'rb') as f:
            response = requests.post("http://localhost:5000/encode-face", 
                                     files={'image': f}, timeout=30)
        if response.status_code == 200:
            embedding = response.json()["embedding"]
    except Exception as e:
        print(f"Embedding failed: {str(e)}")
        return False
    
    if not embedding:
        print("No embedding obtained, cannot continue comparison tests.")
        return False
    
    # Phase 3: Face Comparison Performance  
    print("[COMPARE] Running face comparison benchmark...")
    for i in range(5):
        try:
            start_time = time.time()
            response = requests.post("http://localhost:5000/compare-faces", json={
                "embedding1": embedding,
                "embedding2": embedding
            }, timeout=20)
            end_time = time.time()
            
            if response.status_code == 200:
                time_ms = (end_time - start_time) * 1000
                compare_times.append(time_ms)
                print(f"Run {i+1}: {time_ms:.2f} ms")
            else:
                print(f"Run {i+1}: FAILED ({response.status_code})")
                
        except Exception as e:
            print(f"Run {i+1}: ERROR - {str(e)}")
            return False
    
    # Phase 4: Results Analysis
    print("\n" + "-" * 40)
    print("PERFORMANCE SUMMARY")
    print("-" * 40)
    
    if encode_times:
        print("\nFace Encoding:")
        print(f"  Runs: {len(encode_times)}")
        print(f"  Avg: {statistics.mean(encode_times):.2f} ms")
        print(f"  Min-Max: {min(encode_times):.2f} - {max(encode_times):.2f} ms")
        print(f"  Std Dev: {statistics.stdev(encode_times):.2f} ms")
    
    if compare_times:
        print("\nFace Comparison:")
        print(f"  Runs: {len(compare_times)}")
        print(f"  Avg: {statistics.mean(compare_times):.2f} ms")
        print(f"  Min-Max: {min(compare_times):.2f} - {max(compare_times):.2f} ms")
        print(f"  Std Dev: {statistics.stdev(compare_times):.2f} ms")
    
    # Overall assessment
    encode_avg = statistics.mean(encode_times) if encode_times else 1000
    compare_avg = statistics.mean(compare_times) if compare_times else 100
    
    print("\nOverall Evaluation:")
    if encode_avg < 500 and compare_avg < 50:
        print("  EXCELLENT PERFORMANCE")
    elif encode_avg < 1000 and compare_avg < 100:
        print("  GOOD PERFORMANCE")
    else:
        print("  PERFORMANCE NEEDS IMPROVEMENT")
    
    return True

if __name__ == "__main__":
    test_performance()
