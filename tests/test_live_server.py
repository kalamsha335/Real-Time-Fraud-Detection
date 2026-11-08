import subprocess
import time
import requests
import sys
import json
import os

python_exe = sys.executable
cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

server_process = subprocess.Popen(
    [python_exe, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8008"],
    cwd=cwd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

connected = False
for _ in range(15):
    time.sleep(1)
    if server_process.poll() is not None:
        stdout, stderr = server_process.communicate()
        print("Server process exited prematurely!")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        sys.exit(1)
    try:
        r_health = requests.get("http://127.0.0.1:8008/health", timeout=2)
        if r_health.status_code == 200:
            connected = True
            break
    except Exception:
        pass

if not connected:
    stdout, stderr = server_process.communicate()
    print("Could not connect to server!")
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    sys.exit(1)

try:
    print("GET /health response:", r_health.json())
    assert r_health.json()["status"] == "healthy"

    # Test GET /model/info
    r_info = requests.get("http://127.0.0.1:8008/model/info", timeout=5)
    print("GET /model/info status:", r_info.status_code, "feature_count:", r_info.json()["expected_feature_count"])
    assert r_info.status_code == 200
    assert r_info.json()["expected_feature_count"] == 432

    # Test POST /predict with sample_transaction.json
    with open(os.path.join(os.path.dirname(__file__), "sample_transaction.json"), "r") as f:
        sample_data = json.load(f)

    r_pred = requests.post("http://127.0.0.1:8008/predict", json={"transaction": sample_data}, timeout=5)
    print("POST /predict response:", r_pred.json())
    assert r_pred.status_code == 200
    assert "fraud_probability" in r_pred.json()
    assert "risk_level" in r_pred.json()

    print("\n>>> ALL LIVE HTTP SERVER INTEGRATION TESTS PASSED SUCCESSFULLY! <<<")
finally:
    server_process.terminate()
    server_process.wait()
