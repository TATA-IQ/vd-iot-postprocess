import base64
import json
from datetime import datetime
from io import BytesIO

import cv2
import imutils
import numpy as np
import redis
import requests
from PIL import Image
from src.annotation import AnnotateImage
from src.base_incident import IncidentCreate
from src.cache_verify import VerifyCache
from src.derived_incident import DerivedIncident
from src.detectionclass import DetectionProcess
from src.tracking import Tracker
from templates.brightness_template import BrightnessTemplate
from templates.crowd_template import CrowdTemplate
from templates.ppe_template import PPETemplate


class PostProcessingApp:
    def __init__(self, rcon, logger):
        self.verify_cache = VerifyCache(rcon)
        self.logger = logger

    def convert_image(self, image_str):
        try:
            stream = BytesIO(image_str.encode("ISO-8859-1"))
        except Exception as ex:
            stream = BytesIO(image_str.encode("utf-8"))

        image = Image.open(stream).convert("RGB")

        imagearr = np.array(image)
        return imagearr

    def initialize(self, image, postprocess_config, topic_name, metadata, producer):
        # print(postprocess_config)
        self.topic_name = topic_name
        self.postprocess_config = postprocess_config
        self.image = image
        self.frame = self.convert_image(image)
        self.model_meta = []
        self.computation_meta = []
        self.producer = producer
        self.metadata = metadata
        self.computation_type = ""
        try:
            self.image_name = metadata["image"]["name"]
        except:
            self.image_name = metadata["image_meta"]["name"]

        self.usecase_id = metadata["usecase"]["id"]
        self.camera_id = metadata["hierarchy"]["camera_id"]
        self.image_time = datetime.strptime(metadata["time"]["UTC_time"], "%Y-%m-%d %H:%M:%S.%f")

        # self.usecase_template_id=postprocess_config[self.usecase_id]["usecase_template_id"]

        self.image_height = postprocess_config["image_height"]

        self.usecase_template_id = postprocess_config["usecase_template_id"]
        self.image_width = postprocess_config["image_width"]

        self.legend = postprocess_config["legend"]
        self.incidents = postprocess_config["incidents"]
        self.steps = postprocess_config["steps"]
        self.no_of_steps = len(list(postprocess_config["steps"].keys()))

        current_time = datetime.utcnow()
        time_diff = (current_time - self.image_time).total_seconds()
        self.detection_output = []
        self.incident_output = []
        self.expected_classes = []

        print(f"{self.usecase_id}, {self.camera_id},{self.usecase_template_id}, initialization time, {time_diff}")

        self.logger.info(f"{self.usecase_id}, {self.camera_id}, initialization time, {time_diff}")

    def create_packet(self, image):
        self.metadata["prediction"] = self.detection_output
        self.metadata["incident"] = self.incident_output
        self.metadata["incident_count"] = len(self.incident_output)
        self.metadata["pipeline_inform"]["model_meta"] = {}
        self.metadata["pipeline_inform"]["model_meta"] = self.model_meta
        self.metadata["pipeline_inform"]["computation_meta"] = {}
        self.metadata["pipeline_inform"]["computation_meta"] = self.computation_meta
        image = imutils.resize(image, width=int(self.image_width))
        # image_str=cv2.imencode(".jpg", image)[1].tobytes().decode("ISO-8859-1")

        image_str = base64.b64encode(cv2.imencode(".jpg", image)[1]).decode()
        return {
            "raw_image": image_str,
            "processed_image": image_str,
            "incident_event": self.metadata,
            "usecase": self.metadata["usecase"],
        }

    def callModel(self, url, data):
        # self.model_urls.append(url)
        try:
            response = requests.post(url, json=data)
            current_time = datetime.utcnow()

            time_diff = (current_time - self.image_time).total_seconds()
            self.logger.info(f"{self.usecase_id}, {self.camera_id}, model response time, {time_diff}")
            return response.json()
        except Exception as ex:
            print("====odel call exception====", ex)
            return {}

    def call_template(self):
        if self.usecase_template_id == 4:
            print("====Running for crowd======")
            print(self.expected_classes)
            crowd = CrowdTemplate(self.detection_output, self.expected_classes, self.frame)
            crowd.process_data()

    def create_request(self, model_type, model_framework):
        requestparams = {}
        requestparams["image"] = self.image
        requestparams["image_name"] = self.image_name
        requestparams["camera_id"] = self.camera_id
        requestparams["image_time"] = str(self.image_time)
        requestparams["model_type"] = model_type
        requestparams["model_framework"] = model_framework
        requestparams["model_config"] = {
            "is_track": True,
            "conf_thres": 0.1,
            "iou_thres": 0.1,
            "max_det": 300,
            "agnostic_nms": True,
            "augment": False,
        }
        return requestparams

    def process_step_model(self, url, classes, model_type, model_framework):
        # cv2.imwrite("output/"+self.image_name,self.frame)
        requestparams = self.create_request(model_type, model_framework)
        response = self.callModel(url, requestparams)
        print("======Response=====")
        print(response)

        try:
            detection_result = response["data"]["result"]

        except Exception as ex:
            print("====exception=====", ex)
            detection_result = []
        # print(detection_result)
        print("======*****detection****======", self.image_name)

        self.detection_output.extend(detection_result)

        self.call_template()
        # if len(detection_result)>0:

        #     dp=DetectionProcess(detection_result,classes)

        #     filtered_res=dp.process()
        #     # print("=====filtered======")
        #     # print(filtered_res)
        #     #self.call_template(filtered_res)
        #     self.detection_output.extend(filtered_res)

    def call_annotation(self):
        anot = AnnotateImage(self.expected_classes, self.detection_output, self.frame)
        frame = anot.annotate()
        # if self.usecase_template_id==3:
        #     cv2.imwrite("annot_frame/"+self.image_name,frame)
        return frame

    def call_incident(self):
        incidentres = IncidentCreate(self.incidents, self.detection_output)

        incident_data = incidentres.process()
        if len(incident_data) > 0:
            self.incident_output.extend(incident_data)

    def call_derived_incident(self, step_data, computation_type="brightness"):
        drvd_incident = DerivedIncident(self.detection_output, self.incidents, step_data, computation_type)
        incident = drvd_incident.process_computation_incident()
        self.incident_output.extend(incident)

    def process_step_computation(self):
        frame = np.copy(self.frame)
        print("=====computation=======")

        ids = list(self.incidents.keys())
        print("====ids====", ids)
        if len(ids) > 0:
            uom = [self.incidents[i]["measurement_unit"] for i in ids]
            print("==========uom=========")
            for i in range(0, len(uom)):
                uomtype = uom[i]
                if uomtype.lower() == "count":
                    self.computation_type = "count"
                    pass
                elif uomtype.lower() == "lumen":
                    self.computation_type = "brightness"
                    self.call_template()

                if uomtype.lower() == "kmph":
                    self.computation_type = "kmph"
                    pass

    def process_step(self, steps):
        print("***************")
        print(steps)
        if steps["step_type"] == "model":
            print("====model=====")

            self.expected_classes.extend(list(steps["classes"].values()))

            # metadata["pipeline_inform"]
            self.model_meta.append(
                {
                    "model_url": steps["model_url"],
                    "model_type": steps["model_type"],
                    "model_framework": steps["model_framework"],
                    "model_id": steps["model_id"],
                }
            )
            self.process_step_model(steps["model_url"], steps["classes"], steps["model_type"], steps["model_framework"])
            self.call_incident()
        if steps["step_type"] == "computation":
            self.process_step_computation()
            if len(self.detection_output) > 0:
                self.call_derived_incident(steps, self.computation_type)
            print("======incident derived=======")
            print(self.detection_output)
            print(self.incident_output)

    def process(self):
        if self.no_of_steps == 0:
            pass
        else:
            if int(self.camera_id) == 4 and self.usecase_template_id == 4:
                cv2.imwrite("input/" + self.image_name, self.frame)
                for i in range(1, self.no_of_steps + 1):
                    self.process_step(self.steps[str(i)])

                # frame=self.call_annotation()
                # print("======output====")
                # print(self.incident_output)
                # print(self.detection_output)
                # json_object=json.dumps(self.create_packet(frame))

                # self.producer.send("out_"+self.topic_name,value=json_object)

                # print("Output Send to "+"out_"+self.topic_name)
