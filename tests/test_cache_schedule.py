import redis
import json
pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
r = redis.Redis(connection_pool=pool)
data=r.get("svd_3_2")
print(data)
print(json.loads(data))
