import cv2
import requests
import redis
import base64
import json
import imutils
from PIL import Image
import numpy as np
from io import BytesIO
from datetime import datetime
from src.tracking import Tracker
from templates.crowd_template import CrowdTemplate
from templates.brightness_template import BrightnessTemplate
from src.template_tracking import TemplateTracking
from templates.svd_template import SVDTemplate

from src.grpc_client import GRPCClient
class PostProcessingApp():
    def __init__(self,rcon,logger):
        
        #self.verify_cache=VerifyCache(rcon)
        self.rcon=rcon
        self.logger=logger
        
    
    def convert_image(self,image_str):
        try:
            stream = BytesIO(image_str.encode("ISO-8859-1"))
        except Exception as ex:
            stream = BytesIO(image_str.encode("utf-8"))


        image = Image.open(stream).convert("RGB")

        imagearr=np.array(image)
        return imagearr
    

    def initialize(self,image,postprocess_config,topic_name,metadata,producer):
        #print(postprocess_config)
        self.topic_name=topic_name
        self.grpcclient=GRPCClient()
        self.postprocess_config=postprocess_config
        self.image=image
        self.frame=self.convert_image(image)
        self.model_meta=[]
        self.computation_meta=[]
        self.producer=producer
        self.metadata=metadata
        self.computation_type=""
        try:
            self.image_name=metadata["image"]["name"]
        except:
            self.image_name=metadata["image_meta"]["name"]

        self.usecase_id=metadata["usecase"]["id"]
        self.camera_id=metadata["hierarchy"]["camera_id"]
        self.image_time=datetime.strptime(metadata["time"]["UTC_time"],"%Y-%m-%d %H:%M:%S.%f")
        self.image_height=postprocess_config["image_height"]
        self.usecase_template_id=postprocess_config["usecase_template_id"]
        self.image_width=postprocess_config["image_width"]
        self.legend=postprocess_config["legend"]
        self.incidents=postprocess_config["incidents"]
        self.steps=postprocess_config["steps"]
        self.no_of_steps=len(list(postprocess_config["steps"].keys()))
        current_time=datetime.utcnow()
        time_diff=(current_time-self.image_time).total_seconds()
    
    def call_template(self):
        print("=====Template call for SVD=======")
        #SVD Template
        
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        svd=SVDTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker,self.rcon)
        svd.process_data()

        #Brightness Template
        # bt=BrightnessTemplate(self.image,self.image_name,self.camera_id,self.usecase_id,self.image_time,self.steps,self.frame,self.incidents)
        # bt.process_data()
        #Crowd Template
        # ct=CrowdTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents)
        # ct.process_data()
        #PPE Tempmplate
       
        ppe=PPETemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker,self.rcon)
        ppe.process_data()
    
    def process(self):
        #print("=========",self.camera_id,self.usecase_id)
        if int(self.camera_id)==3 and int(self.usecase_id)==2:
            self.call_template()

    

