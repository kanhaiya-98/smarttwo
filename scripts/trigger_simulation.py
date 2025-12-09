import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def run_simulation():
    print("Triggering Critical Shortage for Paracetamol...")
    try:
        res = requests.post(f"{BASE_URL}/inventory/trigger-procurement", json={
            "medicine_id": 1,
            "quantity": 5000,
            "urgency": "CRITICAL"
        })
        print(f"Trigger Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"Error triggering procurement: {e}")

    print("\nRunning Buyer Agent...")
    try:
        res = requests.post(f"{BASE_URL}/agents/run/BUYER")
        print(f"Buyer Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"Error running Buyer: {e}")

    time.sleep(2)

    print("\nRunning Negotiator Agent...")
    try:
        res = requests.post(f"{BASE_URL}/agents/run/NEGOTIATOR")
        print(f"Negotiator Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"Error running Negotiator: {e}")

if __name__ == "__main__":
    run_simulation()
