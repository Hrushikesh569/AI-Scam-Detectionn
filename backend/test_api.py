import requests
import json

url = "http://localhost:8000/analyze"
payload = {
    "message": "URGENT: Your bank account is locked! Click here to verify",
    "unknown_sender": True
}
response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2))
