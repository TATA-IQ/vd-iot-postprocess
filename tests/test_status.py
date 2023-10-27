import requests

query = {"model_id": 1}
url = "http://localhost:8010/containerstatus"
response = requests.get(url, json=query)
print(response.json())
