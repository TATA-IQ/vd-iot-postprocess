import requests

query = {"model_id": 44, "action": "start"}
url = "http://172.16.0.204:8051/container-service/container"
response = requests.post(url, json=query)
print(response.json())
