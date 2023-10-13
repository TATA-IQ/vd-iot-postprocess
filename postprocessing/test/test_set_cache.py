import redis
import json
pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
r = redis.Redis(connection_pool=pool)
r.set("ddp_6_4",json.dumps(None))
r.set("ddp_4_6",json.dumps(None))
r.set("crowd_6_4",json.dumps(None))
r.set("crowd_4_6",json.dumps(None))
