import base64
import copy
import json
from datetime import datetime
from io import BytesIO
import threading
import cv2
import imutils
import numpy as np
import redis
import requests
from PIL import Image
from src.annotation import AnnotateImage
from src.grpc_client import GRPCClient
from src.mask_images import Masking
from src.template_tracking import TemplateTracking
from src.tracking import Tracker
from templates.anpr import ANPRTemplate
from templates.brightness_template import BrightnessTemplate
from templates.crowd_template import CrowdTemplate
from templates.dedicated_pathway import DedicatedPathway
from templates.fire_smoke import FireSmoke
from templates.garbage import GarbageTemplate
from templates.intrusion import IntrusionTemplate
# from templates.svd_template import SVDTemplate
from templates.ppe_template import PPETemplate
from templates.svd_template import SVDTemplate
from templates.vehicle import VehicleTemplate
from templates.barricade_template import BarricadeTemplate
from templates.persononphone_template import PersononPhoneTemplate
from templates.handrail_template import HandrailTemplate
from console_logging.console import Console
console=Console()
lock=threading.Lock()

class PostProcessingApp:
    def __init__(self, rcon,tracking_server, logger):
        # self.verify_cache=VerifyCache(rcon)
        self.rcon = rcon
    
        self.grpcclient = GRPCClient(tracking_server["host"],tracking_server["port"])
        self.logger = logger

    def convert_image(self, image_str):
        try:
            stream = BytesIO(image_str.encode("ISO-8859-1"))
        except Exception as ex:
            stream = BytesIO(image_str.encode("utf-8"))

        image = Image.open(stream).convert("RGB")

        imagearr = np.array(image)
        return imagearr

    def initialize(self, image, postprocess_config, topic_name, metadata, producer,logger):
        # print(postprocess_config)
        print("=====initialize start=====")
        self.topic_name = topic_name
        
        self.postprocess_config = postprocess_config
        self.image = image
        self.frame = self.convert_image(image)
        self.model_meta = []
        self.process_step_model = []
        self.computation_meta = []
        self.producer = producer
        self.metadata = metadata
        self.computation_type = ""
        self.logger=logger
        try:
            self.image_name = metadata["image"]["name"]
        except:
            self.image_name = metadata["image_meta"]["name"]
        ## cv2.imwrite("input/"+self.image_name,self.frame)

        self.usecase_id = metadata["usecase"]["usecase_id"]
        self.camera_id = metadata["hierarchy"]["camera_id"]
        self.image_time = datetime.strptime(metadata["time"]["UTC_time"], "%Y-%m-%d %H:%M:%S.%f")
        self.image_height = postprocess_config["image_height"]
        self.usecase_template_id = postprocess_config["usecase_template_id"]
        self.image_width = postprocess_config["image_width"]
        self.legend = postprocess_config["legend"]
        self.incidents = postprocess_config["incidents"]
        self.steps = postprocess_config["steps"]
        self.no_of_steps = len(list(postprocess_config["steps"].keys()))
        current_time = datetime.utcnow()
        time_diff = (current_time - self.image_time).total_seconds()
        self.mask_key = None
        if int(self.usecase_template_id) == 11:
            self.mask_key = "intrusion_mask_1"
        if int(self.usecase_template_id) == 9:
            self.mask_key = "dedicated_mask_1"
        self.logger.info(f"Postprocessing starts for camera id {self.camera_id} and usecase id {self.usecase_id}")
        

    def create_packet(self,image_width, image_height,camera_id, usecase_id, metadata,image, detection_output, incident_output,image_name,model_meta,computation_meta):
        self.logger.info(f"creating detection and incident packet for camera id {camera_id} and usecase id {usecase_id}")
        
        metadata["prediction"] = detection_output
        metadata["usecase"]["incident"] = incident_output
        metadata["incident_count"] = len(incident_output)
        print("====len of incident output=====",len(incident_output))
        metadata["pipeline_inform"]["model_meta"] = {}
        metadata["pipeline_inform"]["model_meta"] = model_meta
        metadata["pipeline_inform"]["computation_meta"] = {}
        metadata["pipeline_inform"]["computation_meta"] = computation_meta
        if image_width is None or image_width == 0:
            image = imutils.resize(image, width=int(640))
        else:
            image = imutils.resize(image, width=int(image_width))
        # image_str=cv2.imencode(".jpg", image)[1].tobytes().decode("ISO-8859-1")

        image_str = base64.b64encode(cv2.imencode(".jpg", image)[1]).decode()
        tempname = image_name.split(".")[0]
        # with open("kafkamessages/"+tempname+".txt","w") as f:
        #     f.write(image_str)
        # if len((incident_output))>0:
        #     with open("kafkamessages/"+tempname+".json", "w") as outfile:
        #         json.dump(metadata, outfile)

        return {
            "raw_image": image_str,
            "processed_image": image_str,
            "incident_event": metadata,
            "usecase": metadata["usecase"],
        }
    def create__incident_packet(self,camera_id, usecase_id,metadata, detection_output, incident_output):
        self.logger.info(f"creating incident packet for camera id {camera_id} and usecase id {usecase_id}")
        metadata["prediction"] = detection_output
        metadata["usecase"]["incident"] = incident_output
        metadata["incident_count"] = len(incident_output)
        print("====len of incident output=====",len(incident_output))
        
        
        # image_str=cv2.imencode(".jpg", image)[1].tobytes().decode("ISO-8859-1")

        return {
            
            "incident_event": metadata,
            "usecase": metadata["usecase"],
        }

    def prepare_send(self,image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name, frame ,expected_class, detection_output, incident_out,masked_image, misc_data=None,model_meta=[],computation_meta=[]):
        # cv2.imwrite("post_image/befor_annot/"+image_name,frame)
        self.logger.info(f"Sending data to kafka image name:{image_name},camera id:{camera_id} and usecase id:{usecase_id}")
        print(f"Sending data to kafka image name:{image_name},camera id:{camera_id} and usecase id:{usecase_id}")
        print("======+++++misc___send", camera_id,misc_data)
        if masked_image is not None:
            image_name="masked_"+image_name
            annot = AnnotateImage(expected_class, detection_output, masked_image, misc_data)
        else:
            annot = AnnotateImage(expected_class, detection_output, frame, misc_data)
        if len(detection_output) > 0:
            # print("if===>", len(detection_output))
            frame = annot.annotate(legend,orientation)
        else:
            frame = frame if masked_image is None else masked_image
            frame = annot.annotate(legend,orientation)
        # print("====Annotation done=====")
        print("======+++++misc___after", camera_id,misc_data)
        # cv2.imwrite("post_image/after_annot/"+image_name,frame)
        

        json_objec = json.dumps(self.create_packet(image_width, image_height,camera_id, usecase_id,metadata,frame, detection_output, incident_out, image_name,model_meta,computation_meta))
        producer.send("out_" + topic_name, value=json_objec)
        execution_time=(datetime.utcnow()-image_time).total_seconds()
        self.logger.info(f"Image {image_name} Send to out_{topic_name} event for {camera_id} and usecase id {usecase_id}, with delay {execution_time} on pipeline")
        
        if len(incident_out)>0:
            producer.send("incident_event", value=json.dumps(self.create__incident_packet(camera_id,usecase_id,metadata,detection_output,incident_out)))
            self.logger.info(f"Data Send to topic incident event for {camera_id} and usecase id {usecase_id}")
        del frame
        del json_objec
        del masked_image
        del expected_class
        del detection_output
        del misc_data
        del annot
        print("=====orientation======legend=====",orientation,legend)
        print(f"Image {image_name} Send to out_{topic_name} event for {camera_id} and usecase id {usecase_id}, with delay {execution_time} on pipeline")
        
    def crowd_counting(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        self.logger.info("=====Running crowd=====")
        print("=====Running crowd=====")
        print("crwd====")
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        mask=None
        image_back=None
            
        self.logger.info(f"Crowd counting starts for {camera_id} and usecase id {usecase_id}")
        
        print(f"Crowd counting starts for {camera_id} and usecase id {usecase_id}")
        
        
        detection_output=[]
        incident_out=[]
        expected_class=[] 
        masked_image=None
        misc_data=None
        
        print("=====usecase_id===",usecase_id)
        print("=====template_id===",usecase_template_id)
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                   
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            print("=====crowd processing====")
            ct = CrowdTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker,
                rcon=self.rcon,
                mask=mask,
                image_back=image_back
            )
            # cv2.imwrite("post_image/befor_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image, misc_data = ct.process_data(self.logger)
            # print("%%%%%%%%%%%%%%%%%%%%%%%%")
            # print(detection_output)
            print("======+++++misc___main", camera_id,misc_data)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            self.logger.info(f"Crowd counting done for {camera_id} and usecase id {usecase_id}")
            print(f"Crowd counting done for {camera_id} and usecase id {usecase_id}")
            #del image_name, frame, image, camera_id, usecase_id, incidents,steps,image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            #print("))))))",ex)
            self.logger.info(f"Crowd counting exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
            print(f"Crowd counting exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back,detection_output, incident_out, expected_class, masked_image, misc_data
        lock.release()
        print("+++++crowd complete+++++")

    def anpr_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        
        lock.acquire()
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        mask=None
        misc_data=None
        image_back=None
        self.logger.info(f"Anpr detection starts for {camera_id} and usecase id {usecase_id}")
        print(f"Anpr detection starts for {camera_id} and usecase id {usecase_id}")
        
        print(f"Anpr detection starts for {camera_id} and usecase id {usecase_id}")
        
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                    
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            anpr = ANPRTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker,
                self.rcon,
                mask=mask,
                image_back=image_back
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = anpr.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            self.logger.info(f"Anpr Detect  ends for {camera_id} and usecase id {usecase_id}")
            print(f"Anpr Detect  ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            self.logger.info(f"Anpr Detection exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
            print(f"Anpr Detection exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()
        print("+++++++completed anpr+++++")

    def ppe_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        # metadata=copy.deepcopy(self.metadata)
        #try:
            #metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        mask=None
        misc_data=None
        image_back=None
        self.logger.info(f"PPE detection starts for {camera_id} and usecase id {usecase_id}")
        print(f"PPE detection starts for {camera_id} and usecase id {usecase_id}")
        
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                    
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            ppe = PPETemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker,
                self.rcon,
                mask=mask,
                image_back=image_back
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = ppe.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            
            self.logger.info(f"PPE detection ends for {camera_id} and usecase id {usecase_id}")
            print(f"PPE detection ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            self.logger.info(f"PPE detection exception for {camera_id} and usecase id {usecase_id}, for  exception {ex}")
            print(f"PPE detection exception for {camera_id} and usecase id {usecase_id}, for  exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()
        print("+++++++completed ppe+++++")

    def fire_smoke_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend, orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        
        self.logger.info(f"Fire Smoke detection starts for {camera_id} and usecase id {usecase_id}")
        print(f"Fire Smoke detection starts for {camera_id} and usecase id {usecase_id}")
        
        mask=None
        misc_data=None
        image_back=None
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                    
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            fire = FireSmoke(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker,
                self.rcon,
                mask=mask,
                image_back=image_back
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = fire.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            
            self.logger.info(f"Fire smoke ends for {camera_id} and usecase id {usecase_id}")
            print(f"Fire smoke ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            self.logger.info(f"Fire smoke exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
            print(f"Fire smoke exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()
        print("+++++++completed firesmoke+++++")

    def dedicated_pathway(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        mask=None
        image_back=None
        misc_data=None
        mask_image=None
        
        # try:
            #metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Dedicated pathway starts for {camera_id} and usecase id {usecase_id}")
        console.info(f"Dedicated pathway starts for {camera_id} and usecase id {usecase_id}")
        
        
        # try:
        if boundary_config is not None:
            mask = Masking(
                copy.deepcopy(frame),
                
                usecase_id,
                camera_id,
                usecase_template_id,
                self.rcon,
            )
            
            image_back, mask_image = mask.process_mask(boundary_config)
        tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
        
        ddp = DedicatedPathway(
            image,
            split_image,
            image_name,
            camera_id,
            image_time,
            steps,
            frame,
            incidents,
            usecase_id,
            tracker=tracker,
            rcon=self.rcon,
            mask=mask_image,
            image_back=image_back
        )
        # cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = ddp.process_data(self.logger)
        # cv2.imwrite("post_image/after_det/"+image_name,frame)
        self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, image_back, misc_data)
        
        self.logger.info(f"Dedicated pathway ends for {camera_id} and usecase id {usecase_id}")
        console.success(f"Dedicated pathway ends for {camera_id} and usecase id {usecase_id}")
        # del image_name, frame, image, camera_id, usecase_id, incidents,steps
        # del image_time, metadata,legend, image_time, topic_name
        # except Exception as ex:
        #     self.logger.error(f"Dedicated pathway exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        #     #print(f"Dedicated pathway exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()
        
    
    def intrusion_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        
        lock.acquire()
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        mask=None
        misc_data=None

        image_back=None
        
            #metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Intrusion starts for {camera_id} and usecase id {usecase_id}")
        
        console.info(f"Intrusion starts for {camera_id} and usecase id {usecase_id}")
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                   
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            itr = IntrusionTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker=tracker,
                rcon=self.rcon,
                mask=mask,
                image_back=image_back,
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = itr.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, image_back, misc_data)
            
            self.logger.info(f"Intrusion ends for {camera_id} and usecase id {usecase_id}")
            print(f"Intrusion ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            self.logger.info(f"Intrusion exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
            print(f"Intrusion exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back

        lock.release()

    def handrail_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        
        lock.acquire()
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        mask=None
        misc_data=None

        image_back=None
        
            #metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Handrail starts for {camera_id} and usecase id {usecase_id}")
        
        console.info(f"Handrail starts for {camera_id} and usecase id {usecase_id}")
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                   
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            itr = HandrailTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker=tracker,
                rcon=self.rcon,
                mask=mask,
                image_back=image_back,
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = itr.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, image_back, misc_data)
            
            self.logger.info(f"Handrail ends for {camera_id} and usecase id {usecase_id}")
            print(f"Handrail ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            self.logger.info(f"Handrail exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
            print(f"Handrail exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back

        lock.release()

    def vehicle_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        mask=None
        image_back=None
        misc_data=None
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        
        # metadata=copy.deepcopy(self.metadata)
        # try:
            
            # metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Vehicle Detection starts for {camera_id} and usecase id {usecase_id}")
        print(f"Vehicle Detection starts for {camera_id} and usecase id {usecase_id}")
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                    
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            veh = VehicleTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker=tracker,
                rcon=self.rcon,
                mask=mask,
                image_back=image_back,
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = veh.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            
            self.logger.info(f"Vehicle Detection ends for {camera_id} and usecase id {usecase_id}")
            print(f"Vehicle Detection ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            self.logger.info(f"Vehicle Detection exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
            print(f"Vehicle Detection exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()

    def garbage_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend, orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        mask=None
        image_back=None
        misc_data=None
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        
        # try:
            #metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Garbage Detection starts for {camera_id} and usecase id {usecase_id}")
        print(f"Garbage Detection starts for {camera_id} and usecase id {usecase_id}")
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                    
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            garb = GarbageTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker=tracker,
                rcon=self.rcon,
                mask=mask,
                image_back=image_back
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = garb.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            
            self.logger.info(f"Garbage Detection ends for {camera_id} and usecase id {usecase_id}")
            print(f"Garbage Detection ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
                self.logger.error(f"Garbage Exception ends for {camera_id} and usecase id {usecase_id}, for exception {ex}")
                print(f"Garbage Exception ends for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()

    def persononphone_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend, orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        mask=None
        image_back=None
        misc_data=None
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        
        # try:
            #metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Person on phone Detection starts for {camera_id} and usecase id {usecase_id}")
        print(f"Person on phone  Detection starts for {camera_id} and usecase id {usecase_id}")
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                    
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            garb = PersononPhoneTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker=tracker,
                rcon=self.rcon,
                mask=mask,
                image_back=image_back
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = garb.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            
            self.logger.info(f"Person on phone  Detection ends for {camera_id} and usecase id {usecase_id}")
            print(f"Person on phone  Detection ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
                self.logger.error(f"Person on phone  Exception ends for {camera_id} and usecase id {usecase_id}, for exception {ex}")
                print(f"Person on phone  Exception ends for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()
    def barricade_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend, orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        mask=None
        image_back=None
        misc_data=None
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        
        # try:
            #metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Barricade Detection starts for {camera_id} and usecase id {usecase_id}")
        print(f"Barricade Detection starts for {camera_id} and usecase id {usecase_id}")
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                    
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            garb = BarricadeTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                tracker=tracker,
                rcon=self.rcon,
                mask=mask,
                image_back=image_back
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = garb.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            
            self.logger.info(f"Barricade Detection ends for {camera_id} and usecase id {usecase_id}")
            print(f"Barricade Detection ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
                self.logger.error(f"Barricade Exception ends for {camera_id} and usecase id {usecase_id}, for exception {ex}")
                print(f"Barricade Exception ends for {camera_id} and usecase id {usecase_id}, for exception {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()


    def brightness_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):
        global lock
        lock.acquire()
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        # mask_key=copy.deepcopy(self.mask_key)
        mask=None
        image_back=None
        misc_data=None
        
        try:
            # metadata=copy.deepcopy(self.metadata)
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                   
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            
            self.logger.info(f"Brightness Detection starts for {camera_id} and usecase id {usecase_id}")
            print(f"Brightness Detection starts for {camera_id} and usecase id {usecase_id}")
            
            bt = BrightnessTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                rcon=self.rcon
                
            )
            ## cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image, misc_data = bt.process_data(self.logger)
            ## cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            
            self.logger.info(f"Brightness Detection ends for {camera_id} and usecase id {usecase_id}")
            print(f"Brightness Detection ends for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            self.logger.info(f"Brightness Exception ends for {camera_id} and usecase id {usecase_id}, for ex {ex}")
            print(f"Brightness Exception ends for {camera_id} and usecase id {usecase_id}, for ex {ex}")
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back

        lock.release()

    def svd_detect(self,image_width, image_height, usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta):

        global lock
        lock.acquire()
        # metadata=copy.deepcopy(self.metadata)
        # camera_id=copy.deepcopy(self.camera_id)
        # usecase_id=copy.deepcopy(self.usecase_id)
        mask=None
        image_back=None
        misc_data=None
        
        # frame=copy.deepcopy(self.frame)
        # image_name=copy.deepcopy(self.image_name)
        # metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"SVD Detection starts for {camera_id} and usecase id {usecase_id}")
        print(f"SVD Detection starts for {camera_id} and usecase id {usecase_id}")
        try:
            if boundary_config is not None:
                mask = Masking(
                    copy.deepcopy(frame),
                    
                    usecase_id,
                    camera_id,
                    usecase_template_id,
                    self.rcon,
                )
                print("=====processing mask=====")
                image_back, mask = mask.process_mask(boundary_config)
            tracker = TemplateTracking(usecase_id, camera_id, self.grpcclient)
            svd = SVDTemplate(
                image,
                split_image,
                image_name,
                camera_id,
                image_time,
                steps,
                frame,
                incidents,
                usecase_id,
                boundary_config,
                tracker,
                rcon=self.rcon
            )
            # cv2.imwrite("post_image/before_det/"+image_name,frame)
            detection_output, incident_out, expected_class, masked_image = svd.process_data(self.logger)
            # cv2.imwrite("post_image/after_det/"+image_name,frame)
            self.prepare_send(image_width, image_height,producer,camera_id,usecase_id,image_time,topic_name,legend,orientation,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
            
            # print("====svd incident======")
            # print(incident_out)
            self.logger.info(f"SVD Detection starts for {camera_id} and usecase id {usecase_id}")
            print(f"SVD Detection starts for {camera_id} and usecase id {usecase_id}")
            # del image_name, frame, image, camera_id, usecase_id, incidents,steps
            # del image_time, metadata,legend, image_time, topic_name
        except Exception as ex:
            self.logger.error(f"SVD Detection Exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
            print(f"SVD Detection Exception for {camera_id} and usecase id {usecase_id}, for exception {ex}")
            
        del image_name, frame, image, camera_id, usecase_id, incidents,steps
        del image_time, metadata,legend, topic_name, mask, image_back
        lock.release()

    def call_template(self,image, postprocess_config, topic_name, metadata,boundary_config, producer):
        #print("=====Template call for SVD=======")
        print("======Template Start======")
        detection_output, incident_out = [], []
        mask = None
        image_back = None
        topic_name = topic_name
        
        postprocess_config = postprocess_config
        image = image
        frame = self.convert_image(image)
        model_meta = []
        process_step_model = []
        computation_meta = []
        producer = producer
        metadata = metadata
        computation_type = ""
        #self.logger=logger
        try:
            image_name = metadata["image"]["name"]
        except:
            image_name = metadata["image_meta"]["name"]
        ## cv2.imwrite("input/"+self.image_name,self.frame)

        usecase_id = metadata["usecase"]["usecase_id"]
        camera_id = metadata["hierarchy"]["camera_id"]
        image_time = datetime.strptime(metadata["time"]["UTC_time"], "%Y-%m-%d %H:%M:%S.%f")
        image_height = postprocess_config["image_height"]
        usecase_template_id = postprocess_config["usecase_template_id"]
        image_width = postprocess_config["image_width"]
        legend = postprocess_config["legend"]
        orientation = postprocess_config["orientation"]
        incidents = postprocess_config["incidents"]
        steps = postprocess_config["steps"]
        split_image=postprocess_config["split_image"]
        #no_of_steps = len(list(postprocess_config["steps"].keys()))
        current_time = datetime.utcnow()
        time_diff = (current_time - image_time).total_seconds()
        mask_key = None
        if int(usecase_template_id) == 11:
            mask_key = "intrusion_mask_1"
        if int(usecase_template_id) == 9:
            mask_key = "dedicated_mask_1"
        self.logger.info(f"Postprocessing starts for camera id {camera_id} and usecase id {usecase_id}")
        
        
        if usecase_template_id == 1:
            print("======Template PPE Start======")
            self.ppe_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 3:
            print("======Template FireSmoke Start======")
            self.fire_smoke_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 4:
            print("======Template crowd Start======")
            self.crowd_counting(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 13:
            print("======Template garbage Start======")
            self.garbage_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 8:
            print("======Template brightness Start======")
            self.brightness_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 9:
            print("======Template pathway Start======")
            self.dedicated_pathway(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 10:
            print("======Template anpr Start======")
            self.anpr_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 2:
            print("======Template svd Start======")
            self.svd_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 11:
            print("======Template intrusion Start======")
            self.intrusion_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 12:
            print("======Template vehicle  Start======")
            self.vehicle_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 14:
            self.persononphone_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 15:
            self.barricade_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)
        elif usecase_template_id == 16:
            self.handrail_detect(image_width, image_height,usecase_template_id, metadata,camera_id,usecase_id,image_name,incidents,steps,legend,orientation,topic_name,frame,image,image_time,producer,split_image,boundary_config,model_meta,computation_meta)

        

        # bt=BrightnessTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,rcon=self.rcon)
        # detection_output,incident_out,expected_class, masked_image, misc_data=bt.process_data()
        # print(detection_output)
        # self.crowd_counting(mask,image_back)
        # if int(self.usecase_template_id)==9:
        #     self.dedicated_pathway(mask,image_back)
        # if int(self.usecase_template_id)==1:
        #     self.ppe_detect(mask,image_back)
        # tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        # image,image_name,camera_id,image_time,steps,frame,incidents,usecase_id,tracker=None,rcon=None
        # tracker=TemplateTracking(self.usecase_id,self.camera_id,self.grpcclient)
        # svd=SVDTemplate(self.image,self.image_name,self.camera_id,self.image_time,self.steps,self.frame,self.incidents,self.usecase_id,tracker,rcon=self.rcon)
        # svd.process_data()
        # self.svd_detect(mask,image_back)
        # self.anpr_detect(mask,image_back)

        # print("=======crowd======")
        # self.crowd_counting(mask,image_back)

    def process(self,image, postprocess_config, topic_name, metadata, boundary_config ,producer):
        camera_id = metadata["hierarchy"]["camera_id"]
        usecase_template_id = postprocess_config["usecase_template_id"]

        print("=========", camera_id, usecase_template_id)
        if int(usecase_template_id)==1: #or int(usecase_template_id)==16 or int(usecase_template_id)==14 or int(usecase_template_id)==1: #and :
            # print("====boundary====")
            # print(boundary_config)
            self.call_template(image, postprocess_config, topic_name, metadata, boundary_config ,producer)
        # for steps in list(self.steps.values()):
        #     self.model_meta.append({"model_url":steps["modqel_url"],"model_type":steps["model_type"],"model_framework":steps["model_framework"],"model_id":steps["model_id"]})
        #     #self.process_step_model.append(steps["model_url"],steps["classes"],steps["model_type"],steps["model_framework"])
        # self.call_template()
        # if  int(self.camera_id)==3 and int(self.usecase_template_id)==2:
        #     print(self.usecase_id)
        # self.call_template()
