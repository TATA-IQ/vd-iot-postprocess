"""
Start postprocessing service
"""
import json
import multiprocessing as mp
import consul
# from src.image_encoder import ImageEncoder
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from queue import Queue
import requests
import cv2
import redis
import uvicorn
from fastapi import FastAPI
from kafka import KafkaProducer
from model.query import Query
from shared_memory_dict import SharedMemoryDict
from sourcelogs.logger import create_rotating_log
from src.main import PostProcessingApp
from src.parser import Config
import threading
import socket
os.environ["SHARED_MEMORY_USE_LOCK"] = "1"


app = FastAPI()


manager = mp.Manager()
dicttrack = manager.dict()
queue_image = manager.Queue()

def register_service(consul_conf,port):
    name=socket.gethostname()
    local_ip=socket.gethostbyname(socket.gethostname())
    consul_client = consul.Consul(host=consul_conf["host"],port=consul_conf["port"])
    consul_client.agent.service.register(
    "postprocess",service_id=name,
    port=port,
    address=local_ip,
    tags=["python","postprocess","postprocess"]
    )



def get_confdata(conf):
    res=requests.get(conf[0]["consul_url"])
    data=res.json()
    dbconf =None
    
    postprocessconf=None
    env=None
    consulconf=None
    if "pipelineconfig" in data:
        port=data["pipelineconfig"]["Port"]
        while True:
            endpoints=requests.get("http://pipelineconfig.service.consul:"+str(port)+"/").json()
            #print(endpoints)
            if "modelvalidation" in endpoints["endpoint"]:
                try:
                    postprocessconf=requests.get("http://pipelineconfig.service.consul:"+str(port)+"/"+endpoints["endpoint"]["postprocess"]).json()
                except Exception as ex:
                    print(ex)
                    time.sleep(5)
                    continue
            if "dbapi" in endpoints["endpoint"] and "dbapi" in data:
                try:
                    dbconf=requests.get("http://pipelineconfig.service.consul:"+str(port)+"/"+endpoints["endpoint"]["dbapi"]).json()
                except Exception as ex:
                    print(ex)
                    time.sleep(5)
                    continue
            print(dbconf)
            print(postprocessconf)
            if "kafka" in endpoints["endpoint"]:
                try:
                    kafkaconf=requests.get("http://pipelineconfig.service.consul:"+str(port)+"/"+endpoints["endpoint"]["kafka"]).json()
                except Exception as ex:
                    print(ex)
                    time.sleep(5)
                    continue
            if "consul" in endpoints["endpoint"]:
                try:
                    consulconf=requests.get("http://pipelineconfig.service.consul:"+str(port)+"/"+endpoints["endpoint"]["consul"]).json()
                except Exception as ex:
                    print(ex)
                    time.sleep(5)
                    continue
            print(dbconf)
            print(postprocessconf)
            if dbconf is not None and postprocessconf is not None and kafkaconf is not None:
                break
    print("******")
    print(dbconf)
    return  dbconf,postprocessconf,kafkaconf,consulconf
conf = Config.yamlconfig("config/config.yaml")
_,postprocessconf,_,_=get_confdata(conf)
redis_server=postprocessconf["redis"]
pool = redis.ConnectionPool(host=redis_server["host"], port=redis_server["port"], db=0)
r_con = redis.Redis(connection_pool=pool)


def future_callback_error_logger(future):
    '''
    Log future error
    Args:
        future (future object): future object
    '''
    e = future.exception()

    print("*****", e)


def connect_producer(kafkahost):
    """
    Connect with Kafka
    Args:
        kakahost (list): list of kafka broker
    returns:
        producer (object): Kafka producer object
    """
    producer = KafkaProducer(bootstrap_servers=kafkahost, value_serializer=lambda x: json.dumps(x).encode("utf-8"))
    return producer


def submit_task(postprocess, kafkahost,logger):
    '''
    Start Postprocessing
    Args:
        postprocess (dict): postprocess configuration
        kakahost (list): list of kafka prober
    '''
    producer = connect_producer(kafkahost)
    while True:
        if not queue_image.empty():
            data = queue_image.get()
            # print("===got data===",data)

            #postprocess.initialize(data[0], data[1], data[2], data[3], producer,logger)
            postprocess.process(data[0], data[1], data[2], data[3],data[4] ,producer)
            # postprocess.process(data[0],data[1],data[2],data[3])
        # else:
        # 	print("queue seems to be empty")



def process_queue(kafkahost,tracking_server,logger):
    '''
    Submit Task for the upcoming request from preprocess module
    '''
    print("====starting queue====")
    
    postprocess = PostProcessingApp(r_con,tracking_server, logger)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(0,10):
            # lock.acquire()
            f1 = executor.submit(submit_task, postprocess, kafkahost,logger)
            f1.add_done_callback(future_callback_error_logger)
            #lock.release()


@app.post("/postprocess")
async def process_image(data: Query):
    '''
    Api for postprocessing
    data (Query): Query from the api
    '''
    print("Imagr got")
    queue_image.put([data.image, data.postprocess_config, data.topic_name, data.metadata,data.boundary_config])
    return {"data": ["image pushed"]}
    # postprocess=PostProcessingApp(data.image,data.postprocess_config,data.topic_name,data.metadata)
    # postprocess.process(r_con)


def run_uvicorn(port):
    '''
    Run API Server
    '''
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    '''
    Main function for postprocessing
    '''
    print("=====inside main************")
    logg = create_rotating_log("logs/logs.log")
    conf = Config.yamlconfig("config/config.yaml")
    dbconf,postprocessconf,kafkaconf,consulconf=get_confdata(conf)
    register_service(consulconf,postprocessconf["port"])
    kafkahost = kafkaconf["kafka"]
    tracking_server=postprocessconf["tracking_server"]
    redis_server=postprocessconf["redis"]
    tracker_smd = SharedMemoryDict(name="tracking", size=10000000)
    tracker_smd.shm.close()
    tracker_smd.shm.unlink()  # Free and release the shared memory block at the very end
    logger = create_rotating_log("logs/log.log")
    del tracker_smd
    print("====redis====")
    print(redis_server)
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        try:
            f2 = executor.submit(run_uvicorn,postprocessconf["port"])
            f2.add_done_callback(future_callback_error_logger)
            
            print("f1====")
            for i in range(0,5):
                f1 = executor.submit(process_queue, kafkahost,tracking_server,logger)
                f1.add_done_callback(future_callback_error_logger)
            
        except KeyboardInterrupt:
            tracker_smd = SharedMemoryDict(name="tracking", size=10000000)
            tracker_smd.shm.close()
            tracker_smd.shm.unlink()  # Free and release the shared memory block at the very end
            del tracker_smd
    print("=====queue started===")

    