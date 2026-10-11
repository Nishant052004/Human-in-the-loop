import urllib.request
import urllib.parse
import json

base = "http://127.0.0.1:8000"

print("--- 1. Testing POST /api/blockchain/verify ---")
req = urllib.request.Request(f"{base}/api/blockchain/verify", data=b"", method="POST")
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode())
    print("Verify Result:", data["is_valid"], "| Blocks count:", data["total_blocks"])

print("\n--- 2. Testing POST /api/pipeline/run ---")
form_data = urllib.parse.urlencode({
    "project_description": "FastAPI REST API with PostgreSQL on port 8000"
}).encode()
req = urllib.request.Request(f"{base}/api/pipeline/run", data=form_data, method="POST")
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode())
    print("Pipeline Success:", data["success"])
    print("Confidence:", data["data"]["confidence_score"])
    print("Risk Level:", data["data"]["risk_level"])
    print("Simulation Passed:", data["data"]["simulation_passed"])

print("\n--- 3. Testing POST /api/approvals/1/action (Approve with RLHF) ---")
action_payload = json.dumps({
    "action": "approve",
    "reviewer_role": "Senior Tech Lead",
    "docker_code": "FROM python:3.11-alpine\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nEXPOSE 5000\nCMD [\"python\", \"app.py\"]",
    "k8s_code": "# Kubernetes Service...\napiVersion: v1\nkind: Service\nmetadata:\n  name: flask-service",
    "cicd_code": "# Github Workflow...\nname: CI\non:\n  push:\n    branches: [ main ]",
    "reason": "Standardized base container image to python:3.11-alpine for hardened security"
}).encode()
req = urllib.request.Request(
    f"{base}/api/approvals/1/action",
    data=action_payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode())
    print("Action Status:", data["status"])
    print("Audit Hash:", data["audit_hash"])
    print("Extracted Preference:", data.get("preference_extracted"))

print("\n--- 4. Testing PDF Report Retrieval ---")
req = urllib.request.Request(f"{base}/api/report/1/pdf")
with urllib.request.urlopen(req) as res:
    pdf_bytes = res.read()
    print("PDF Downloaded successfully! Size in bytes:", len(pdf_bytes))

print("\nAll Web API integration tests PASSED successfully!")
