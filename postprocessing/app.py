from src.main import PostProcessingApp
from sourcelogs.logger import create_rotating_log
import redis
import cv2
from kafka import KafkaProducer
from fastapi import FastAPI
from queue import Queue
from model.query import Query
import uvicorn
import multiprocessing as mp
from src.parser import Config
import json

# from src.image_encoder import ImageEncoder
import os
from shared_memory_dict import SharedMemoryDict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

os.environ["SHARED_MEMORY_USE_LOCK"] = "1"


app = FastAPI()
pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
r_con = redis.Redis(connection_pool=pool)
manager = mp.Manager()
dicttrack = manager.dict()
queue_image = manager.Queue()
logger = create_rotating_log("logs/log.log")


def future_callback_error_logger(future):
    e = future.exception()

    print("*****", e)


def connect_producer(kafkahost):
    producer = KafkaProducer(bootstrap_servers=kafkahost, value_serializer=lambda x: json.dumps(x).encode("utf-8"))
    return producer


def submit_task(postprocess, kafkahost):
    producer = connect_producer(kafkahost)
    while True:
        if not queue_image.empty():
            data = queue_image.get()
            # print("===got data===",data)

            postprocess.initialize(data[0], data[1], data[2], data[3], producer)
            postprocess.process()
            # postprocess.process(data[0],data[1],data[2],data[3])
        # else:
        # 	print("queue seems to be empty")


def process_queue(kafkahost):
    print("====starting queue====")
    with ThreadPoolExecutor(max_workers=2) as executor:
        postprocess = PostProcessingApp(r_con, logger)
        f1 = executor.submit(submit_task, postprocess, kafkahost)
        f1.add_done_callback(future_callback_error_logger)


@app.post("/postprocess")
async def process_image(data: Query):
    print("Imagr got")
    queue_image.put([data.image, data.postprocess_config, data.topic_name, data.metadata])
    return {"data": ["image pushed"]}
    # postprocess=PostProcessingApp(data.image,data.postprocess_config,data.topic_name,data.metadata)
    # postprocess.process(r_con)


def run_uvicorn():
    uvicorn.run(app, host="0.0.0.0", port=int(8007))


if __name__ == "__main__":
    print("=====inside main************")
    data = Config.yamlconfig("config/config.yaml")
    kafkahost = data[0]["kafka"]
    tracker_smd = SharedMemoryDict(name="tracking", size=10000000)
    tracker_smd.shm.close()
    tracker_smd.shm.unlink()  # Free and release the shared memory block at the very end
    del tracker_smd
    with ProcessPoolExecutor(max_workers=2) as executor:
        try:
            f1 = executor.submit(process_queue, kafkahost)
            print("f1====")
            f2 = executor.submit(run_uvicorn)

            f1.add_done_callback(future_callback_error_logger)
            f2.add_done_callback(future_callback_error_logger)
        except KeyboardInterrupt:
            tracker_smd = SharedMemoryDict(name="tracking", size=10000000)
            tracker_smd.shm.close()
            tracker_smd.shm.unlink()  # Free and release the shared memory block at the very end
            del tracker_smd
    print("=====queue started===")

    process_queue()
