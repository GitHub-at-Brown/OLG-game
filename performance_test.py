"""
Performance test script for OLG game server.
This script sends multiple requests to the server and measures response times.
"""
import time
import requests
import statistics
import concurrent.futures
import json

# Server address
BASE_URL = "http://localhost:5001"

def time_request(url, method="GET", data=None):
    """Time a request to a URL."""
    start_time = time.time()
    
    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, json=data)
    
    end_time = time.time()
    return {
        "url": url,
        "method": method,
        "status_code": response.status_code,
        "time": end_time - start_time,
        "response_size": len(response.content)
    }

def run_test(test_name, url, method="GET", data=None, num_requests=50, concurrent=10):
    """Run a test with multiple requests."""
    print(f"\nRunning test: {test_name}")
    print(f"URL: {url}")
    print(f"Method: {method}")
    print(f"Number of requests: {num_requests}")
    print(f"Concurrent requests: {concurrent}")
    
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
        futures = []
        for i in range(num_requests):
            futures.append(executor.submit(time_request, url, method, data))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error: {e}")
    
    # Sort results by time
    results.sort(key=lambda x: x["time"])
    
    # Calculate statistics
    times = [result["time"] for result in results]
    mean_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = times[int(0.95 * len(times))]
    
    # Print results
    print("\nResults:")
    print(f"Mean response time: {mean_time:.4f} s")
    print(f"Median response time: {median_time:.4f} s")
    print(f"Min response time: {min_time:.4f} s")
    print(f"Max response time: {max_time:.4f} s")
    print(f"95th percentile response time: {p95_time:.4f} s")
    
    return {
        "test_name": test_name,
        "results": {
            "mean": mean_time,
            "median": median_time,
            "min": min_time,
            "max": max_time,
            "p95": p95_time
        }
    }

def main():
    """Run performance tests."""
    results = []
    
    # Test 1: Get current state (no user ID)
    results.append(run_test("Get current state (professor view)", 
                           f"{BASE_URL}/api/current_state"))
    
    # Test 2: Submit decision (young borrowing)
    for i in range(10):
        user_id = f"test_user_{i}"
        data = {
            "user_id": user_id,
            "decision_type": "borrow",
            "amount": 10.0,
            "demand_curve": [
                {"interestRate": 0, "borrowingAmount": 40},
                {"interestRate": 5, "borrowingAmount": 20},
                {"interestRate": 10, "borrowingAmount": 5}
            ]
        }
        results.append(run_test(f"Submit young borrowing decision (user {i})", 
                               f"{BASE_URL}/api/submit_decision", 
                               method="POST", 
                               data=data,
                               num_requests=10,  # Fewer requests as this is costly
                               concurrent=5))
    
    # Test 3: Advance round
    results.append(run_test("Advance round", 
                           f"{BASE_URL}/api/advance_round", 
                           method="POST", 
                           data={"force": True},
                           num_requests=5,  # Even fewer as this is very costly
                           concurrent=1))  # Only one at a time
    
    # Save results to a file
    with open("performance_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nPerformance tests complete. Results saved to performance_results.json")

if __name__ == "__main__":
    main() 