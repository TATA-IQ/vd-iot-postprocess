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
import copy
# from templates.svd_template import SVDTemplate
from templates.ppe_template import PPETemplate
from src.mask_images import Masking
from templates.dedicated_pathway import DedicatedPathway
from templates.anpr import ANPRTemplate
from src.grpc_client import GRPCClient
from src.annotation import AnnotateImage
from templates.fire_smoke import FireSmoke
from templates.vehicle import VehicleTemplate
from templates.svd_template import SVDTemplate

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
        self.process_step_model=[]
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
        self.mask_key=None
        if int(self.usecase_template_id)==11:
            self.mask_key="intrusion_mask_1"
        if int(self.usecase_template_id)==9:
            self.mask_key="dedicated_mask_1"
        

        
    def create_packet(self,image,detection_output,incident_output):
        self.metadata["prediction"]=detection_output
        self.metadata["incident"]=incident_output
        self.metadata["incident_count"]=len(incident_output)
        self.metadata["pipeline_inform"]["model_meta"]={}
        self.metadata["pipeline_inform"]["model_meta"]=self.model_meta
        self.metadata["pipeline_inform"]["computation_meta"]={}
        self.metadata["pipeline_inform"]["computation_meta"]=self.computation_meta
        if self.image_width is None or self.image_width==0:
            image=imutils.resize(image,width=int(640))
        else:
            image=imutils.resize(image,width=int(self.image_width))
        #image_str=cv2.imencode(".jpg", image)[1].tobytes().decode("ISO-8859-1")

        image_str=base64.b64encode(cv2.imencode('.jpg', image)[1]).decode()
        tempname=self.image_name.split(".")[0]
        # with open("kafkamessages/"+tempname+".txt","w") as f:
        #     f.write(image_str)
        # with open("kafkamessages/"+tempname+".json", "w") as outfile:
        #     json.dump(self.metadata, outfile)

        return {"raw_image":image_str,"processed_image":image_str,"incident_event":self.metadata,"usecase":self.metadata["usecase"]}


    def prepare_send(self,expected_class,detection_output,incident_out,masked_image,misc_data=None):
        if masked_image is not None:
            annot=AnnotateImage(expected_class,detection_output,masked_image,misc_data)
        else:
            annot=AnnotateImage(expected_class,detection_output,self.frame,misc_data)
        if len(detection_output)>0:
            print("if===>",len(detection_output))
            frame=annot.annotate(self.legend)
        else:
            frame=self.frame if masked_image is None else masked_image
        print("====Annotation done=====")
        cv2.imwrite("output//"+str(self.usecase_id)+"_"+self.image_name,frame)
        json_objec=json.dumps(self.create_packet(frame,detection_output,incident_out))
        self.producer.send("out_"+self.topic_name,value=json_objec)
        print(f"=====Data Sent to out_{self.topic_name}=======")

    

    def crowd_counting(self,mask,image_back):
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
           
        ct=CrowdTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,rcon=self.rcon)
        detection_output,incident_out,expected_class, masked_image,misc_data=ct.process_data()
        print("%%%%%%%%%%%%%%%%%%%%%%%%")
        print(detection_output)
        self.prepare_send(expected_class,detection_output,incident_out,masked_image,misc_data)
    
    def anpr_detect(self,mask,image_back):
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        anpr=ANPRTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker,self.rcon)
        detection_output,incident_out,expected_class, masked_image=anpr.process_data()
        self.prepare_send(expected_class,detection_output,incident_out,masked_image)
    def ppe_detect(self,mask,image_back):
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        ppe=PPETemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker,self.rcon)
        detection_output,incident_out,expected_class, masked_image=ppe.process_data()
        self.prepare_send(expected_class,detection_output,incident_out,masked_image)
    def fire_smoke_detect(self,mask,image_back):
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        fire=FireSmoke(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker,self.rcon)
        detection_output,incident_out,expected_class, masked_image=fire.process_data()
        self.prepare_send(expected_class,detection_output,incident_out,masked_image)
    
    def dedicated_pathway(self,mask,image_back):
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        ddp=DedicatedPathway(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker=tracker,rcon=self.rcon,mask=mask,image_back=image_back)
        detection_output,incident_out,expected_class, masked_image=ddp.process_data()
        self.prepare_send(expected_class,detection_output,incident_out,image_back)

    def intrusion_detect(self,mask,image_back):
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        itr=IntrusionTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker=tracker,rcon=self.rcon,mask=mask,image_back=image_back)
        detection_output,incident_out,expected_class, masked_image=itr.process_data()
        self.prepare_send(expected_class,detection_output,incident_out,image_back)
    def vehicle_detect(self,mask,image_back):
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        veh=VehicleTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker=tracker,rcon=self.rcon,mask=mask,image_back=image_back)
        detection_output,incident_out,expected_class, masked_image=veh.process_data()
        self.prepare_send(expected_class,detection_output,incident_out,image_back)
    
    def garbage_detect(self,mask,image_back):
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        garb=GarbageTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker=tracker,rcon=self.rcon,mask=mask,image_back=image_back)
        detection_output,incident_out,expected_class, masked_image=garb.process_data()
        self.prepare_send(expected_class,detection_output,incident_out,image_back)
    def brightness_detect(self, mask, image_back):
        bt=BrightnessTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,rcon=self.rcon)
        detection_output,incident_out,expected_class, masked_image, misc_data=bt.process_data()
        self.prepare_send(expected_class,detection_output,incident_out,image_back,misc_data)



    
      


    def call_template(self):
        print("=====Template call for SVD=======")
        detection_output,incident_out=[],[]
        mask=None
        image_back=None
        if self.mask_key is not None:
            print("====Maksing Called=====")
            mask=Masking(copy.deepcopy(self.frame),self.mask_key,self.usecase_id,self.camera_id,self.usecase_template_id,self.rcon)
            print("=====processing mask=====")
            image_back,mask=mask.process_mask()
            print("=====processing masked=====")
        # if self.usecase_template_id==1:
        #     self.ppe_detect(mask,image_back)
        # if self.usecase_template_id==3:
        #     self.fire_smoke_detect(mask,image_back)
        # if self.usecase_template_id==4:
        #     self.crowd_counting(mask,image_back)
        # if self.usecase_template_id==7:
        #     self.garbage_detect(mask,image_back)
        # if self.usecase_template_id==8:
        #     self.brightness_detect(mask,image_back)
        # if self.usecase_template_id==9:
        #     self.dedicated_pathway(mask,image_back)
        # if self.usecase_template_id==10:
        #     self.anpr_detect(mask,image_back)

        # bt=BrightnessTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,rcon=self.rcon)
        # detection_output,incident_out,expected_class, masked_image, misc_data=bt.process_data()
        # print(detection_output)
        #self.crowd_counting(mask,image_back)
        # if int(self.usecase_template_id)==9:
        #     self.dedicated_pathway(mask,image_back)
        # if int(self.usecase_template_id)==1:
        #     self.ppe_detect(mask,image_back)
        # tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        svd=SVDTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker,rcon=self.rcon)
        svd.process_data()
        
        # print("=======crowd======")
        # self.crowd_counting(mask,image_back)


        
        
        
        
        
        

    
    def process(self):
        print("=========",self.camera_id,self.usecase_template_id)
        # if ( int(self.camera_id)==6) and int(self.usecase_id)==4:
        #     self.call_template()
        # for steps in list(self.steps.values()):
        #     self.model_meta.append({"model_url":steps["modqel_url"],"model_type":steps["model_type"],"model_framework":steps["model_framework"],"model_id":steps["model_id"]})
        #     #self.process_step_model.append(steps["model_url"],steps["classes"],steps["model_type"],steps["model_framework"])
        # self.call_template()
        # if  int(self.camera_id)==3 and int(self.usecase_template_id)==2:
        #     print(self.usecase_id)
        self.call_template()

    

