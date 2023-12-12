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
    consul_client = consul.Consul(host=consul_conf["host"],port=int(consul_conf["port"]))
    consul_client.agent.service.register(
    "postprocess",service_id=name+"-postrocess-"+consul_conf["env"],
    port=int(port),
    address=local_ip,
    tags=["python","postprocess",consul_conf["env"]]
)

def get_service_address(consul_client,service_name,env):
    while True:
        
        try:
            services=consul_client.catalog.service(service_name)[1]
            print(services)
            for i in services:
                if env == i["ServiceID"].split("-")[-1]:
                    return i
        except:
            time.sleep(10)
            continue
def get_confdata(consul_conf):
    consul_client = consul.Consul(host=consul_conf["host"],port=consul_conf["port"])
    pipelineconf=get_service_address(consul_client,"pipelineconfig",consul_conf["env"])

    
    
    env=consul_conf["env"]
    
    endpoint_addr="http://"+pipelineconf["ServiceAddress"]+":"+str(pipelineconf["ServicePort"])
    print("endpoint addr====",endpoint_addr)
    while True:
        
        try:
            res=requests.get(endpoint_addr+"/")
            endpoints=res.json()
            print("===got endpoints===",endpoints)
            break
        except Exception as ex:
            print("endpoint exception==>",ex)
            time.sleep(10)
            continue
    
    while True:
        try:
            res=requests.get(endpoint_addr+endpoints["endpoint"]["postprocess"])
            postprocessconf=res.json()
            print("postprocessconf===>",postprocessconf)
            break
            

        except Exception as ex:
            print("postprocessconf exception==>",ex)
            time.sleep(10)
            continue
    while True:
        try:
            res=requests.get(endpoint_addr+endpoints["endpoint"]["kafka"])
            kafkaconf=res.json()
            print("kafkaconf===>",kafkaconf)
            break
            

        except Exception as ex:
            print("kafkaconf exception==>",ex)
            time.sleep(10)
            continue
    print("=======searching for dbapi====")
    while True:
        try:
            print("=====consul search====")
            dbconf=get_service_address(consul_client,"dbapi",consul_conf["env"])
            print("****",dbconf)
            dbhost=dbconf["ServiceAddress"]
            dbport=dbconf["ServicePort"]
            res=requests.get(endpoint_addr+endpoints["endpoint"]["dbapi"])
            dbres=res.json()
            print("===got db conf===")
            print(dbres)
            break
        except Exception as ex:
            print("db discovery exception===",ex)
            time.sleep(10)
            continue
    for i in dbres["apis"]:
        print("====>",i)
        dbres["apis"][i]="http://"+dbhost+":"+str(dbport)+dbres["apis"][i]

    
    print("======dbres======")
    print(dbres)
    print(postprocessconf)
    print(kafkaconf)
    return  dbres,postprocessconf,kafkaconf




conf = Config.yamlconfig("config/config.yaml")
_,postprocessconf,kafkaconf=get_confdata(conf[0]["consul"])
register_service(conf[0]["consul"],postprocessconf["port"])
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
    dbconf,postprocessconf,kafkaconf=get_confdata(conf[0]["consul"])
    register_service(conf[0]["consul"],postprocessconf["port"])
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

    