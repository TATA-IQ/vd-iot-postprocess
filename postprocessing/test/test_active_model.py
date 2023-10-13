import requests
url=" http://127.0.0.1:8009/active_model"

response=requests.post(url,json={"model_id":"1"})
print(response.json())