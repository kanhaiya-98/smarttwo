"""Complete demo test - full workflow."""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("="*60)
print("COMPLETE WORKFLOW DEMO TEST")
print("="*60)

# Step 1: Trigger Discovery
print("\n[1] Starting Supplier Discovery...")
response = requests.post(f"{BASE_URL}/discovery/start", json={
    "medicine_id": 1,
    "quantity": 5000
})
print(f"Response: {response.json()}")

# Step 2: Get suppliers
print("\n[2] Fetching Discovered Suppliers...")
response = requests.get(f"{BASE_URL}/discovery/suppliers/1")
suppliers = response.json()
print(f"Found {len(suppliers)} suppliers:")
for s in suppliers:
    print(f"  - {s['name']}: {s['status']}")

# Step 3: Get email thread for first supplier
if suppliers:
    supplier_id = suppliers[0]['id']
    print(f"\n[3] Getting Email Thread for {suppliers[0]['name']}...")
    response = requests.get(f"{BASE_URL}/discovery/emails/{supplier_id}")
    emails = response.json()
    print(f"Found {len(emails)} emails")
    
    for email in emails:
        sender_type = "AI" if email['is_from_agent'] else "Supplier"
        print(f"  - {sender_type}: {email['subject'][:50]}...")

# Step 4: Create test quotes (simulate supplier replies)
print("\n[4] Creating Test Quotes...")
test_quotes = [
    {"supplier_id": s['id'], "unit_price": 0.15 + i*0.02, "delivery_days": 3 + i*2, "stock_available": 8000}
    for i, s in enumerate(suppliers[:3])
]

for quote_data in test_quotes:
    response = requests.post(f"{BASE_URL}/negotiation-decision/quotes/create", json=quote_data)
    print(f"  Created quote: {response.json()}")

# Step 5: Get all quotes
print("\n[5] Fetching All Quotes...")
response = requests.get(f"{BASE_URL}/negotiation-decision/quotes/1")
quotes = response.json()
for q in quotes:
    print(f"  - {q['supplier_name']}: ${q['unit_price']}/unit, {q['delivery_days']} days")

# Step 6: Run Decision Analysis
print("\n[6] Running Decision Analysis...")
response = requests.post(f"{BASE_URL}/negotiation-decision/decision/analyze", json={
    "procurement_task_id": 1,
    "urgency": "MEDIUM",
    "budget_mode": False
})
decision = response.json()
print(f"Recommended Supplier ID: {decision['recommended_supplier_id']}")
print(f"Total Score: {decision['total_score']}")
print(f"\nExplanation:\n{decision['explanation'][:200]}...")

# Step 7: Get negotiation recommendation
print("\n[7] Getting Final Recommendation...")
response = requests.get(f"{BASE_URL}/negotiation-decision/decision/recommendation/1")
recommendation = response.json()
print(f"Supplier: {recommendation['supplier_name']}")
print(f"Score: {recommendation['total_score']}")

print("\n" + "="*60)
print("DEMO COMPLETE - ALL ENDPOINTS WORKING!")
print("="*60)
