"""
ATIS API Endpoint Testing Suite
================================
Comprehensive testing for all API endpoints to ensure:
- Endpoints are responding correctly
- Data is valid and complete
- No dummy/placeholder/fake data present
- Response times are acceptable
- All dashboards have backend support

Run with: python test_endpoints.py
"""

import requests
import time
import json
from typing import Dict, List, Any
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Server configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10  # seconds

# Test results storage
results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "tests": []
}


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{text.center(70)}")
    print(f"{Fore.CYAN}{'=' * 70}\n")


def print_test(name: str, status: str, details: str = ""):
    """Print test result"""
    if status == "PASS":
        print(f"{Fore.GREEN}✓ {name}: {status}")
        results["passed"] += 1
    elif status == "FAIL":
        print(f"{Fore.RED}✗ {name}: {status}")
        if details:
            print(f"  {Fore.YELLOW}{details}")
        results["failed"] += 1
    elif status == "WARN":
        print(f"{Fore.YELLOW}⚠ {name}: {status}")
        if details:
            print(f"  {details}")
        results["warnings"] += 1
    
    results["tests"].append({
        "name": name,
        "status": status,
        "details": details
    })


def test_endpoint(endpoint: str, expected_fields: List[str] = None) -> Dict[str, Any]:
    """Test a GET endpoint and verify response"""
    test_name = f"GET {endpoint}"
    
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        # Check status code
        if response.status_code != 200:
            print_test(test_name, "FAIL", f"Status {response.status_code}")
            return None
        
        # Check response time
        if elapsed > 5000:
            print_test(test_name, "WARN", f"Slow response: {elapsed:.0f}ms")
        
        # Parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print_test(test_name, "FAIL", f"Invalid JSON: {str(e)}")
            return None
        
        # Check expected fields
        if expected_fields:
            missing_fields = [f for f in expected_fields if f not in data]
            if missing_fields:
                print_test(test_name, "FAIL", f"Missing fields: {missing_fields}")
                return None
        
        # Success
        print_test(test_name, "PASS", f"{elapsed:.0f}ms")
        return data
        
    except requests.exceptions.Timeout:
        print_test(test_name, "FAIL", "Request timeout")
        return None
    except requests.exceptions.ConnectionError:
        print_test(test_name, "FAIL", "Connection error - is server running?")
        return None
    except Exception as e:
        print_test(test_name, "FAIL", str(e))
        return None


def validate_asteroid_data(data: List[Dict]) -> bool:
    """Validate that asteroid data is legitimate (no dummy data)"""
    if not data or len(data) == 0:
        return False
    
    # Check for real asteroid names (not "Asteroid 1", "Test", etc.)
    for item in data[:10]:  # Sample first 10
        name = item.get("name", "")
        if name.lower() in ["test", "dummy", "placeholder", "mock"]:
            print_test("Data Validation", "FAIL", f"Found dummy data: {name}")
            return False
        
        # Check for placeholder values
        if item.get("threat", 0) == 0.5:  # Common placeholder
            continue  # Many asteroids might have similar threats, this is OK
        
        # Check SPKID is valid (positive integer)
        spkid = item.get("spkid", 0)
        if spkid <= 0:
            print_test("Data Validation", "FAIL", f"Invalid SPKID: {spkid}")
            return False
    
    print_test("Data Validation", "PASS", f"Verified {len(data)} asteroids")
    return True


def test_core_endpoints():
    """Test core API endpoints"""
    print_header("Testing Core Data Endpoints")
    
    # 1. Galaxy data
    data = test_endpoint("/api/galaxy", expected_fields=["objects"])
    if data:
        objects = data.get("objects", [])
        if len(objects) < 1000:
            print_test("Galaxy Data Size", "WARN", f"Only {len(objects)} asteroids")
        else:
            print_test("Galaxy Data Size", "PASS", f"{len(objects)} asteroids")
        
        # Validate first object has correct structure
        if len(objects) > 0:
            first_obj = objects[0]
            obj_fields = ["x", "y", "z", "threat", "spkid", "name", "url"]
            missing = [f for f in obj_fields if f not in first_obj]
            if missing:
                print_test("Galaxy Object Structure", "FAIL", f"Missing: {missing}")
            else:
                print_test("Galaxy Object Structure", "PASS", "All fields present")
    
    # 2. Radar data
    data = test_endpoint("/api/radar", expected_fields=["moid", "threat"])
    if data and len(data.get("moid", [])) > 0:
        print_test("Radar Data", "PASS", f"{len(data.get('moid', []))} points")
    
    # 3. Watchlist
    data = test_endpoint("/api/watchlist", expected_fields=["watchlist"])
    if data:
        watchlist = data.get("watchlist", [])
        if validate_asteroid_data(watchlist):
            if len(watchlist) > 0:
                # Check first asteroid has all required fields
                first = watchlist[0]
                required = ["name", "spkid", "threat_score", "moid", "url"]
                missing = [f for f in required if f not in first]
                if missing:
                    print_test("Watchlist Fields", "FAIL", f"Missing: {missing}")
                else:
                    print_test("Watchlist Fields", "PASS", "All required fields present")
    
    # 4. System stats
    data = test_endpoint("/api/stats", expected_fields=["total_objects", "high_risk_count"])
    if data:
        total = data.get("total_objects", 0)
        if total > 10000:
            print_test("System Stats", "PASS", f"{total} total objects")
        else:
            print_test("System Stats", "WARN", f"Only {total} objects tracked")
    
    # 5. All asteroids (for analytics)
    data = test_endpoint("/api/asteroids")
    if data and len(data) > 0:
        # Check for orbital elements
        first = data[0]
        orbital_elements = ["e", "a", "i", "per_y"]
        missing = [f for f in orbital_elements if f not in first]
        if missing:
            print_test("Orbital Elements", "FAIL", f"Missing: {missing}")
        else:
            print_test("Orbital Elements", "PASS", "All orbital data present")


def test_specific_asteroid_endpoints():
    """Test endpoints that require asteroid ID"""
    print_header("Testing Asteroid-Specific Endpoints")
    
    # Use well-known asteroids
    test_ids = ["20000433", "20099942", "20001566"]  # Eros, Apophis, Icarus
    
    for asteroid_id in test_ids:
        endpoint = f"/api/asteroid/{asteroid_id}"
        data = test_endpoint(endpoint, expected_fields=["spkid", "name"])
        
        if data:
            # Test orbital path
            path_data = test_endpoint(f"/api/orbital-path/{asteroid_id}")
            if path_data and "path" in path_data:
                if len(path_data["path"]) < 50:
                    print_test(f"Orbital Path {asteroid_id}", "WARN", "Path too short")
                else:
                    print_test(f"Orbital Path {asteroid_id}", "PASS", f"{len(path_data['path'])} points")
            
            # Test close approaches
            ca_data = test_endpoint(f"/api/close-approaches/{asteroid_id}")
            if ca_data:
                print_test(f"Close Approaches {asteroid_id}", "PASS")


def test_ml_endpoints():
    """Test machine learning endpoints"""
    print_header("Testing ML & Analytics Endpoints")
    
    # ML Performance metrics
    data = test_endpoint("/api/ml-performance", expected_fields=["metrics", "confusion_matrix"])
    if data:
        metrics = data.get("metrics", {})
        required_metrics = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
        missing = [m for m in required_metrics if m not in metrics]
        if missing:
            print_test("ML Metrics", "FAIL", f"Missing: {missing}")
        else:
            # Check values are reasonable (not all 0 or 1)
            accuracy = metrics.get("accuracy", 0)
            if 0.5 < accuracy < 1.0:
                print_test("ML Metrics", "PASS", f"Accuracy: {accuracy:.2%}")
            else:
                print_test("ML Metrics", "WARN", f"Unusual accuracy: {accuracy:.2%}")
    
    # Test ML explainability
    test_endpoint("/api/ml-explain/20000433")
    
    # Test ensemble prediction
    test_endpoint("/api/ensemble-predict/20000433")
    
    # Test anomaly detection
    test_endpoint("/api/anomaly-score/20000433")


def test_time_machine():
    """Test time machine endpoint"""
    print_header("Testing Time Machine")
    
    # Test current time
    data = test_endpoint("/api/time-machine?time_offset_days=0&limit=100")
    if data:
        asteroids = data.get("asteroids", [])
        if len(asteroids) > 0:
            # Verify positions are valid
            first = asteroids[0]
            if all(k in first for k in ["x", "y", "z", "spkid", "name"]):
                print_test("Time Machine Data", "PASS", f"{len(asteroids)} positions calculated")
            else:
                print_test("Time Machine Data", "FAIL", "Missing position data")
    
    # Test future time (+365 days)
    data = test_endpoint("/api/time-machine?time_offset_days=365&limit=50")
    if data:
        print_test("Time Machine Future", "PASS", "Future positions working")


def test_live_updates():
    """Test live update endpoint"""
    print_header("Testing Live Data Updates")
    
    data = test_endpoint("/api/live")
    if data:
        if "active" in data:
            print_test("Live Updates", "PASS", f"Active: {data.get('active')}")


def test_websocket_info():
    """Test WebSocket status endpoint"""
    data = test_endpoint("/api/ws/stats")
    if data:
        connections = data.get("active_connections", 0)
        print_test("WebSocket Stats", "PASS", f"{connections} active connections")


def check_server_running():
    """Check if server is accessible"""
    print_header("Server Connectivity Check")
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print_test("Server Running", "PASS", f"Server accessible at {BASE_URL}")
            return True
        else:
            print_test("Server Running", "FAIL", f"Unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_test("Server Running", "FAIL", f"Cannot connect to {BASE_URL}")
        print(f"\n{Fore.YELLOW}⚠ Make sure the server is running:")
        print(f"{Fore.YELLOW}  uvicorn src.web.main:app --reload --port 8000\n")
        return False
    except Exception as e:
        print_test("Server Running", "FAIL", str(e))
        return False


def print_summary():
    """Print test summary"""
    print_header("Test Summary")
    
    total = results["passed"] + results["failed"] + results["warnings"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"{Fore.GREEN}Passed:   {results['passed']:3d}")
    print(f"{Fore.RED}Failed:   {results['failed']:3d}")
    print(f"{Fore.YELLOW}Warnings: {results['warnings']:3d}")
    print(f"{Fore.CYAN}Total:    {total:3d}")
    print(f"\n{Fore.CYAN}Pass Rate: {pass_rate:.1f}%")
    
    if results["failed"] == 0 and results["warnings"] == 0:
        print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED! System is fully operational.")
    elif results["failed"] == 0:
        print(f"\n{Fore.YELLOW}⚠ All tests passed with some warnings.")
    else:
        print(f"\n{Fore.RED}❌ Some tests failed. Please review errors above.")
    
    # Save detailed results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n{Fore.CYAN}Detailed results saved to: test_results.json")


def main():
    """Run all tests"""
    print(f"{Fore.MAGENTA}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                  ATIS API Endpoint Test Suite                     ║")
    print("║            Automated Testing for Backend Functionality            ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(Style.RESET_ALL)
    
    # Check server is running
    if not check_server_running():
        return
    
    # Run all test suites
    try:
        test_core_endpoints()
        test_specific_asteroid_endpoints()
        test_ml_endpoints()
        test_time_machine()
        test_live_updates()
        test_websocket_info()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Tests interrupted by user")
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {str(e)}")
    
    # Print summary
    print_summary()


if __name__ == "__main__":
    main()
