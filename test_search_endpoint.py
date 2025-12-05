import requests
import json

response = requests.post(
    'http://127.0.0.1:5000/api/search',
    json={'ingredient': 'sugar', 'storefront': 'fresh'}
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
