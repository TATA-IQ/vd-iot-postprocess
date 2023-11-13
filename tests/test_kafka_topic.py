from kafka import KafkaConsumer
import json
#1_3_2
brokers=["172.16.0.175:9092"
   ,"172.16.0.171:9092"
  , "172.16.0.174:9092"]
consumer = KafkaConsumer(
        "out_" + "2_4_16",
        bootstrap_servers=brokers,
        auto_offset_reset="latest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="out" + "2_4_16",
    )
for i in consumer:
    print(i)