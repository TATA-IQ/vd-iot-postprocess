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

# from templates.svd_template import SVDTemplate
from templates.ppe_template import PPETemplate
from templates.svd_template import SVDTemplate
from templates.vehicle import VehicleTemplate

lock=threading.Lock()

class PostProcessingApp:
    def __init__(self, rcon, logger):
        # self.verify_cache=VerifyCache(rcon)
        self.rcon = rcon
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
        
        self.topic_name = topic_name
        self.grpcclient = GRPCClient()
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
        #cv2.imwrite("input/"+self.image_name,self.frame)

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
        self.logger.info(f"Postprocessing starts for camera id {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        

    def create_packet(self, metadata,image, detection_output, incident_output):
        self.logger.info(f"creating detection and incident packet for camera id {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        metadata["prediction"] = detection_output
        metadata["usecase"]["incident"] = incident_output
        metadata["incident_count"] = len(incident_output)
        print("====len of incident output=====",len(incident_output))
        metadata["pipeline_inform"]["model_meta"] = {}
        metadata["pipeline_inform"]["model_meta"] = self.model_meta
        metadata["pipeline_inform"]["computation_meta"] = {}
        metadata["pipeline_inform"]["computation_meta"] = self.computation_meta
        if self.image_width is None or self.image_width == 0:
            image = imutils.resize(image, width=int(640))
        else:
            image = imutils.resize(image, width=int(self.image_width))
        # image_str=cv2.imencode(".jpg", image)[1].tobytes().decode("ISO-8859-1")

        image_str = base64.b64encode(cv2.imencode(".jpg", image)[1]).decode()
        tempname = self.image_name.split(".")[0]
        # with open("kafkamessages/"+tempname+".txt","w") as f:
        #     f.write(image_str)
        # with open("kafkamessages/"+tempname+".json", "w") as outfile:
        #     json.dump(self.metadata, outfile)

        return {
            "raw_image": image_str,
            "processed_image": image_str,
            "incident_event": metadata,
            "usecase": metadata["usecase"],
        }
    def create__incident_packet(self,metadata, detection_output, incident_output):
        self.logger.info(f"creating incident packet for camera id {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        metadata["prediction"] = detection_output
        metadata["usecase"]["incident"] = incident_output
        metadata["incident_count"] = len(incident_output)
        print("====len of incident output=====",len(incident_output))
        
        
        # image_str=cv2.imencode(".jpg", image)[1].tobytes().decode("ISO-8859-1")

        return {
            
            "incident_event": metadata,
            "usecase": metadata["usecase"],
        }

    def prepare_send(self,image_time,topic_name,legend,metadata,image_name, frame ,expected_class, detection_output, incident_out, masked_image, misc_data=None):
        #cv2.imwrite("post_image/befor_annot/"+image_name,frame)
        self.logger.info(f"Sending data to kafka{self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        if masked_image is not None:
            annot = AnnotateImage(expected_class, detection_output, masked_image, misc_data)
        else:
            annot = AnnotateImage(expected_class, detection_output, frame, misc_data)
        if len(detection_output) > 0:
            print("if===>", len(detection_output))
            frame = annot.annotate(legend)
        else:
            frame = frame if masked_image is None else masked_image
        print("====Annotation done=====")
        #cv2.imwrite("output//"+image_name,frame)
        print("AAAA" * 10)
        print(detection_output)

        json_objec = json.dumps(self.create_packet(metadata,frame, detection_output, incident_out))
        self.producer.send("out_" + topic_name, value=json_objec)
        self.logger.info(f"Data Send to out_{topic_name} event for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        if len(incident_out)>0:
            self.producer.send("incident_event", value=json.dumps(self.create__incident_packet(metadata,detection_output,incident_out)))
            self.logger.info(f"Data Send to topic incident event for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        execution_time=(datetime.utcnow()-image_time).total_seconds()
        
        print(f"=====Data Sent to out_{topic_name}=======with delay {execution_time}")

    def crowd_counting(self, mask, image_back):
        global lock
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Crowd counting starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        print(f"Crowd counting starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        
        
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        image_name=copy.deepcopy(self.image_name)
        frame=copy.deepcopy(self.frame)
        #metadata=copy.deepcopy(self.metadata)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        ct = CrowdTemplate(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            rcon=self.rcon,
        )
        #cv2.imwrite("post_image/befor_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image, misc_data = ct.process_data()
        print("%%%%%%%%%%%%%%%%%%%%%%%%")
        print(detection_output)
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image, misc_data)
        self.logger.info(f"Crowd counting done for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def anpr_detect(self, mask, image_back):
        global lock
        
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Anpr detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        print(f"Anpr detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        print(f"Anpr detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        

        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        #metadata=copy.deepcopy(self.metadata)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        anpr = ANPRTemplate(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            tracker,
            self.rcon,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = anpr.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image)
        self.logger.info(f"Crowd counting ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def ppe_detect(self, mask, image_back):
        global lock
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"PPE detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        print(f"PPE detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        metadata=copy.deepcopy(self.metadata)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        ppe = PPETemplate(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            tracker,
            self.rcon,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = ppe.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image)
        self.logger.info(f"PPE detection ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def fire_smoke_detect(self, mask, image_back):
        global lock
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Fire Smoke detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        print(f"Fire Smoke detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        #metadata=copy.deepcopy(self.metadata)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        fire = FireSmoke(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            tracker,
            self.rcon,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = fire.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image)
        self.logger.info(f"Fire smoke ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def dedicated_pathway(self, mask, image_back):
        global lock
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Dedicated pathway starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        print(f"Dedicated pathway starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        #metadata=copy.deepcopy(self.metadata)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        ddp = DedicatedPathway(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            tracker=tracker,
            rcon=self.rcon,
            mask=mask,
            image_back=image_back,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = ddp.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,frame,expected_class, detection_output, incident_out, image_back)
        self.logger.info(f"Dedicated pathway ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def intrusion_detect(self, mask, image_back):
        global lock
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Intrusion starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        print(f"Intrusion starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        #metadata=copy.deepcopy(self.metadata)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        itr = IntrusionTemplate(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            tracker=tracker,
            rcon=self.rcon,
            mask=mask,
            image_back=image_back,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = itr.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        
        self.prepare_send(image_time,topic_name,legend,metadata, image_name,frame,expected_class, detection_output, incident_out, image_back)
        self.logger.info(f"Intrusion ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def vehicle_detect(self, mask, image_back):
        global lock
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Vehicle Detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        print(f"Vehicle Detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        #metadata=copy.deepcopy(self.metadata)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        veh = VehicleTemplate(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            tracker=tracker,
            rcon=self.rcon,
            mask=mask,
            image_back=image_back,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = veh.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,expected_class, detection_output, incident_out, image_back)
        self.logger.info(f"Vehicle Detection ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def garbage_detect(self, mask, image_back):
        global lock
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        self.logger.info(f"Garbage Detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        print(f"Garbage Detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        

        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        garb = GarbageTemplate(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            tracker=tracker,
            rcon=self.rcon,
            mask=mask,
            image_back=image_back,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = garb.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,frame,expected_class, detection_output, incident_out, image_back)
        self.logger.info(f"Garbage Detection ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def brightness_detect(self, mask, image_back):
        global lock
        lock.acquire()
        metadata=copy.deepcopy(self.metadata)
        
        self.logger.info(f"Brightness Detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        print(f"Brightness Detection starts for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        bt = BrightnessTemplate(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            rcon=self.rcon,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image, misc_data = bt.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,frame,expected_class, detection_output, incident_out, image_back, misc_data)
        self.logger.info(f"Brightness Detection ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        print(f"Brightness Detection ends for {self.camera_id} and usecase id {str(metadata['usecase']['usecase_id'])}")
        
        lock.release()

    def svd_detect(self, mask, image_back):
        global lock
        lock.acquire()
        frame=copy.deepcopy(self.frame)
        image_name=copy.deepcopy(self.image_name)
        metadata=copy.deepcopy(self.metadata)
        legend=copy.deepcopy(self.legend)
        image_time=copy.deepcopy(self.image_time)
        topic_name=copy.deepcopy(self.topic_name)
        tracker = TemplateTracking(self.usecase_id, self.camera_id, self.grpcclient)
        svd = SVDTemplate(
            self.image,
            image_name,
            self.camera_id,
            self.image_time,
            self.steps,
            frame,
            self.incidents,
            self.usecase_id,
            tracker,
            rcon=self.rcon,
        )
        #cv2.imwrite("post_image/before_det/"+image_name,frame)
        detection_output, incident_out, expected_class, masked_image = svd.process_data()
        #cv2.imwrite("post_image/after_det/"+image_name,frame)
        
        self.prepare_send(image_time,topic_name,legend,metadata,image_name,frame,expected_class, detection_output, incident_out, masked_image)
        print("====svd incident======")
        print(incident_out)
        lock.release()

    def call_template(self):
        #print("=====Template call for SVD=======")
        detection_output, incident_out = [], []
        mask = None
        image_back = None
        if self.mask_key is not None:
            print("====Maksing Called=====")
            mask = Masking(
                copy.deepcopy(self.frame),
                self.mask_key,
                self.usecase_id,
                self.camera_id,
                self.usecase_template_id,
                self.rcon,
            )
            print("=====processing mask=====")
            image_back, mask = mask.process_mask()
            print("=====processing masked=====")
        if self.usecase_template_id == 1:
            self.ppe_detect(mask, image_back)
        if self.usecase_template_id == 3:
            self.fire_smoke_detect(mask, image_back)
        if self.usecase_template_id == 4:
            self.crowd_counting(mask, image_back)
        if self.usecase_template_id == 13:
            self.garbage_detect(mask, image_back)
        if self.usecase_template_id == 8:
            self.brightness_detect(mask, image_back)
        if self.usecase_template_id == 9:
            self.dedicated_pathway(mask, image_back)
        if self.usecase_template_id == 10:
            self.anpr_detect(mask, image_back)
        if self.usecase_template_id == 2:
            self.svd_detect(mask, image_back)
        if self.usecase_template_id == 11:
            self.intrusion_detect(mask, image_back)
        if self.usecase_template_id == 12:
            self.vehicle_detect(mask, image_back)

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

    def process(self):
        print("=========", self.camera_id, self.usecase_template_id)
        #if  int(self.usecase_template_id)==11: #and int(self.camera_id)==6:
        self.call_template()
        # for steps in list(self.steps.values()):
        #     self.model_meta.append({"model_url":steps["modqel_url"],"model_type":steps["model_type"],"model_framework":steps["model_framework"],"model_id":steps["model_id"]})
        #     #self.process_step_model.append(steps["model_url"],steps["classes"],steps["model_type"],steps["model_framework"])
        # self.call_template()
        # if  int(self.camera_id)==3 and int(self.usecase_template_id)==2:
        #     print(self.usecase_id)
        # self.call_template()
