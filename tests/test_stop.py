import requests

query = {"model_id": 1}
url = "http://localhost:8010/stopcontainer"
response = requests.post(url, json=query)
print(response.json())
