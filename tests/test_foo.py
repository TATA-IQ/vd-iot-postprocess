import requests
data={"image":"",
    "postprocess_config":{},
    "topic_name": "test",
    "metadata":{}
    }
resp=requests.post("http://localhost:8005/postprocess",json=data)
print(resp.json())