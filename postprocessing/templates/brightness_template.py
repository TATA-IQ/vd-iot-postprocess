"""
Brightness Template
"""
from src.cache import Caching
from src.common_template import Template
from src.incidents import IncidentExtract
from src.postprocessing_template import PostProcessing
import numpy as np


class BrightnessTemplate(Template, PostProcessing,IncidentExtract, Caching):
    def __init__(self, image, image_name, camera_id, image_time, steps, frame, incidents, usecase_id, rcon=None):
        """
        Brightness Template Initilization
        Args:
            image (str): image in string
            image_name (str): name of image
            camera_id (str): camera id
            image_time (str): time of image captured
            steps (dict): all the steps of usecase
            frame (np.array): image as numpy array
            incidents (list): incidents list of usecase
            usecase_id (str or int): usecase id
            tracker (object): tracker object
            rcon (object): redis connection
            mask (np.array): mask image 1
            image_back (np.array): mask image2

        """
        print("====Initializing crowd=====")
        self.frame = image
        self.allsteps = steps
        self.incidents = incidents
        self.rcon = rcon
        self.usecase_id = usecase_id
        Template.__init__(self, image, image_name, camera_id, image_time, steps, frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self, self.rcon)
            print("====Caching INitilaize done")
            data = self.getbykey("brightness", self.camera_id, self.usecase_id)
            if data is None:
                self.initialize_cache()
            incident_cache= self.getbykey("incident_crowd", self.camera_id, self.usecase_id)
            if incident_cache is None:
                self.initialize_incident_cache()
        print("Brightness initialization done")

    def initialize_cache(self):
        """
        cache initialization
        """
        cachedict = {}
        cachedict["detections"] = []

    def set_cache(self, currentdata, cachedict):
        '''
        Store data to cache
        Args:
            currentdata (dict): current frame detection
            cachedict (list): cache data

        '''
        if cachedict is not None:
            if len(cachedict["detections"]) > 9:
                print(len(cachedict))
                for i in range(10, len(cachedict["detections"])):
                    del cachedict["detections"][i]

                cachedict["detections"].insert(0, currentdata)
            else:
                cachedict["detections"].insert(0, currentdata)
        else:
            cachedict = {}
            cachedict["detections"] = []
            cachedict["detections"].insert(0, currentdata)
        self.setbykey("brightness", self.camera_id, self.usecase_id, cachedict)
    def initialize_incident_cache(self):
        """
        cache initialization incident
        """
        cachedict = {}

        cachedict["incidents"] = []
        self.setbykey("incident_brightness", self.camera_id, self.usecase_id, cachedict)
        print("======cache initialized====")

    def set_cache_incident(self,  cachedict,currentdata):
        '''
        Store data to cache incident
        Args:
            currentdata (dict): current frame detection
            cachedict (list): cache data

        '''
        print("===Storing in cache====")
        print(cachedict)
        print(currentdata)
        if len(cachedict["incidents"])>0 :
            if len(cachedict["incidents"]) > 10:
                print(len(cachedict))
                for i in range(9, len(cachedict["incidents"])):
                    cachedict["incidents"].pop()

                cachedict["incidents"].insert(0, currentdata)
            else:
                print("=====storing cachedict======")
                cachedict["incidents"].insert(0, currentdata)
        else:
            cachedict = {}
            cachedict["incidents"] = []
            print("===Storing firsr data cache====")

            cachedict["incidents"].insert(0, currentdata)
        print("***********")
        print(cachedict)
        self.setbykey("incident_brightness", self.camera_id, self.usecase_id, cachedict)
    
    def filter_misc_incidents(self,cachedict_incident,current_incidents):
        #cachedict_incident = self.getbykey("incident_crowd", self.camera_id, self.usecase_id)
        old_incident_list=sum(cachedict_incident["incidents"],[])
        # [old_incident_list.extend(i["misc"]) for i in cachedict_incident]
        inclist=[]
        indxlist=[]
        commonindxlist=[]
        print("=====incident cache====",cachedict_incident)
        if len(cachedict_incident["incidents"] )>0:
            for idx,ctd in enumerate(current_incidents):
                indxlist.append(idx)
                for cachinc in old_incident_list:
                    cach_misc=cachinc["misc"]
                    ctd_misc=ctd["misc"]
                    for misc_ctd in ctd_misc:
                        for misc_cach in cach_misc:
                            if misc_cach["text"]==misc_ctd["text"] and np.abs(float(misc_cach["data"])-float(misc_ctd["data"]))>2:
                                commonindxlist.append(idx)
                            
        
            
        else:
            print("======Returning current incidents======")
            inclist= current_incidents
        if len(commonindxlist)>0:
            print("========common index list====",commonindxlist)
            indxlist=list(set(indxlist)^set(commonindxlist))
            print("=====lsit to report======",indxlist)
            indxlist=list(set(indxlist))
            inclist=[current_incidents[i] for i in indxlist]

        #self.set_cache_incident(cachedict_incident,current_incidents)
        return inclist,current_incidents

    
    def process_data(self,logger):
        '''
        Process Vrightness Template
        Args:
            logger (object): Logger object
        returns:
            detection_data (list): list of detection data
            incident_dict (list): list of incident data
            self.expected_class (list): list of expected class
            masked_image (np.array): masked image as numpy array
        '''
        #print("==============Data==========")
        logger.info(f"Template Brightness: Detection for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        print(f"Template Brightness: Brightness for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        
        filtered_res_dict = {}

        filtered_res_dict = self.process_steps()
        print("====filtered res dict=====",filtered_res_dict)
        # print("====Process called=======")
        # print(filtered_res_dict)
        cachedict = self.getbykey("brightness", self.camera_id, self.usecase_id)
        print("-=====cache ====")
        print(cachedict)
        if cachedict is None or len(cachedict)>0:
            self.initialize_cache()
        else:
            PostProcessing.__init__(self, filtered_res_dict, cachedict["detections"])
        print(self.incidents)
        print(self.allsteps)
        IncidentExtract.__init__(self, filtered_res_dict, self.incidents, self.allsteps)
        print("======incident initialized======")
        incident_dict, detected_output = self.process_incident()
        print("======incident_dict======")
        print(incident_dict)
        if len(incident_dict)>0:
            print("====len of incident before filter====",len(incident_dict))
            cachedict_incident=self.getbykey("incident_brightness", self.camera_id, self.usecase_id)
            incident_dict,current_incidents=self.filter_misc_incidents(cachedict_incident,incident_dict)
            
            self.set_cache_incident(cachedict_incident,current_incidents)
            print("====len of incident after filter====",len(incident_dict))
        logger.info(f"Template Brightness:Incident Extracted: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        print(f"Template Brightness:Incident Extracted: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        
        print("=========incident dict======")
        print(incident_dict)
        if "misc" in filtered_res_dict:
            if len(filtered_res_dict) > 0:
                misc_data = filtered_res_dict["misc"]
        # print("=====filtered res dict Brightness====")
        # print(filtered_res_dict)
        # if "prediction_class" in filtered_res_dict and len(detection_incidentflag["prediction_class"]) > 0:
        #     #print("====updating cache======")
        self.set_cache(filtered_res_dict, cachedict)
        logger.info(f"Template Brightness:completed: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        print(f"Template Brightness:completed: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        return [], incident_dict, self.expected_class, None, misc_data
