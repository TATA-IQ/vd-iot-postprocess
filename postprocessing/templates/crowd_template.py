from src.cache import Caching
from src.common_template import Template
from src.compute import Computation
from src.incidents import IncidentExtract
from src.postprocessing_template import PostProcessing
import copy


class CrowdTemplate(Template, PostProcessing, IncidentExtract, Caching):
    def __init__(
        self,
        image,
        image_name,
        camera_id,
        image_time,
        steps,
        frame,
        incidents,
        usecase_id,
        tracker=None,
        rcon=None,
        mask=None,
        image_back=None,
    ):
        """
        ANPR Template Initilization
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
        self.usecase_id = usecase_id
        self.tracker = tracker
        self.mask = mask
        self.image_back = image_back
        self.rcon = rcon
        Template.__init__(self, image, image_name, camera_id, image_time, steps, frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self, self.rcon)
            print("====Caching INitilaize done")
            data = self.getbykey("crowd", self.camera_id, self.usecase_id)
            incident_cache= self.getbykey("incident_crowd", self.camera_id, self.usecase_id)
            if incident_cache is None:
                self.initialize_incident_cache()
            if data is None:
                print("===initializnge cache====")
                self.initialize_cache()
                print("====cache initialized====")

    def initialize_cache(self):
        """
        cache initialization
        """
        cachedict = {}

        cachedict["detections"] = []
        self.setbykey("crowd", self.camera_id, self.usecase_id, cachedict)
        print("======cache initialized====")
    
    def set_cache(self, currentdata, cachedict):
        '''
        Store data to cache
        Args:
            currentdata (dict): current frame detection
            cachedict (list): cache data

        '''
        if cachedict is not None:
            if len(cachedict["detections"]) > 10:
                print(len(cachedict))
                for i in range(9, len(cachedict["detections"])):
                    cachedict["detections"].pop()

                cachedict["detections"].insert(0, currentdata)
            else:
                cachedict["detections"].insert(0, currentdata)
        else:
            cachedict = {}
            cachedict["detections"] = []
            cachedict["detections"].insert(0, currentdata)
        self.setbykey("crowd", self.camera_id, self.usecase_id, cachedict)
    def initialize_incident_cache(self):
        """
        cache initialization incident
        """
        cachedict = {}

        cachedict["incidents"] = []
        self.setbykey("incident_crowd", self.camera_id, self.usecase_id, cachedict)
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
        self.setbykey("incident_crowd", self.camera_id, self.usecase_id, cachedict)
    def process_steps(self):
        '''
        Process the steps of usecase id
        returns :
            final_prediction (dict): filtered result based on preprocessing
            masked_image (dict): numpy array image
        '''
        final_prediction = {}
        masked_image = None
        steps_keys = list(map(lambda x: int(x), list(self.steps.keys())))
        steps_keys.sort()
        # print("========steps keys extracted=====")
        for ki in steps_keys:
            step = self.steps[str(ki)]
            if step["step_type"] == "model":
                self.expected_class.extend(list(step["classes"].values()))
                # print("=======inside model===")
                self.model_call(step)
                # print("====inside step model===")
                if len(self.detected_class) > 0:
                    self.detection_init(self.detected_class, self.expected_class, self.image_time)

                    filtered_res = self.process_detection()
                    if self.tracker is not None:
                        filtered_res = self.tracker.track(self.image, filtered_res)
                    self.filtered_output.extend(filtered_res)
                    print("=====length of detection===", len(filtered_res))
                    final_prediction["prediction_class"] = self.filtered_output
                if self.mask is not None:
                    final_prediction["prediction_class"], masked_image = self.masked_detection(
                        self.mask, self.image_back, final_prediction["prediction_class"]
                    )
                    print("=====masked perdiction=====")
                    print(final_prediction["prediction_class"])
            if step["step_type"] == "computation":
                Computation.__init__(self, final_prediction, step, self.frame)
                print("====final prediction before count====")
                print(final_prediction)
                final_prediction = self.count_crowd()
                print("======prediction after count=====")
                print(final_prediction)
        return final_prediction, masked_image

    def derived_incident(self, idx, step):
        class_name = self.incident_class[idx]
        icident_value = self.incident_values[idx]
        detected_output = []
        print("====checking derived incidentt====")

        if "prediction_class" in self.detection_output and len(self.detection_output["prediction_class"]) > 0:
            detected_output = self.detection_output["prediction_class"]

        print("======derived incident====")

        upper_limit = float(step["upper_limit"])
        lower_limit = float(step["lower_limit"])
        tolerance = float(step["tolerance"])

        upper_limit = upper_limit + (upper_limit) * (tolerance)
        lower_limit = lower_limit - (lower_limit) * (tolerance)
        incident_list = []
        print("======self misc=====")
        print(self.misc)
        print(class_name)

        if self.misc is not None:
            print("====inside misc===")
            for i in self.misc:
                val = i["data"]
                text = i["text"]
                if val >= upper_limit or val <= lower_limit:
                    incident_list.append({"data": val, "text": text})

        if len(incident_list) > 0:
            return self.create_derived_incident(idx, incident_list), detected_output
        else:
            return [], detected_output

    def process_incident(self):
        print("=====own class incident=====")
        incidentlist, detectin_incidentflag = [], []
        print("*******incident_type_id*******")
        print(self.incident_type_id)
        for idx, inc_id in enumerate(self.incident_type_id):
            print("=======checking incident=======")
            # if int(inc_id) == 2:
            for st in self.derived_steps:
                tempderived_incident, detectin_incidentflag = self.derived_incident(idx, st)
                print("====incidebts====")
                print(tempderived_incident)
                if len(tempderived_incident) > 0:
                    incidentlist.extend(tempderived_incident)
        print("=====Returning=====")
        return incidentlist, detectin_incidentflag

    
                
                
    def process_data(self,logger):
        '''
        Process Crowd Template
        Args:
            logger (object): Logger object
        returns:
            detection_data (list): list of detection data
            incident_dict (list): list of incident data
            self.expected_class (list): list of expected class
            masked_image (np.array): masked image as numpy array
        '''
        detection_data = []
        incident_dict=[]
        detection_incidentflag = {}
        print("==============Data==========")
        filtered_res_dict = {}
        logger.info(f"Template Crowd: Detection for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        print(f"Template Crowd: Detection for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        
        filtered_res_dict, masked_image = self.process_steps()


        
        cachedict = self.getbykey("crowd", self.camera_id, self.usecase_id)
        
        
        if cachedict is None or len(cachedict) == 0:
            self.initialize_cache()
            logger.info(f"Template Crowd:Reinitialized cache, len of cache: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            print(f"Template Crowd:Reinitialized cache, len of cache: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            
        else:
            # print("======postprocessing called======")
            # print(cachedict)
            # print(filtered_res_dict)
            logger.info(f"Template Crowd:Postprocessing called: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            print(f"Template Crowd:Postprocessing called: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            PostProcessing.__init__(self, filtered_res_dict, cachedict["detections"])
            filtered_res_dict["prediction_class"], _ = self.filter_data_detection()
            logger.info(f"Template Crows:Postprocessing Done: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            print(f"Template Crowd:Postprocessing Done: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        print("=======filtering======")
        if "prediction_class" in filtered_res_dict:
            detection_data = filtered_res_dict["prediction_class"]
            IncidentExtract.__init__(self, filtered_res_dict, self.incidents, self.allsteps)
            incident_dict, detection_incidentflag["prediction_class"] = self.process_incident()
            logger.info(f"Template Crowd:Incident Extracted: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            print(f"Template Crowd:Incident Extracted: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        # print("*******incident_dict*****")
        # print(incident_dict)
        incident_dict_copy=copy.deepcopy(incident_dict)
        if len(incident_dict)>0:
            print("====len of incident before filter====",len(incident_dict))
            cachedict_incident=self.getbykey("incident_crowd", self.camera_id, self.usecase_id)
            incident_dict,current_incidents=self.filter_misc_incidents(cachedict_incident,incident_dict)
            
            self.set_cache_incident(cachedict_incident,current_incidents)
            print("====len of incident after filter====",len(incident_dict))
        # print("=========incident dict======")
        # print(incident_dict)
        # print("=======detection data====")
        # print(len(detection_data))
        misc_data = None
        if len(incident_dict_copy)>0:
            
            misc_data = incident_dict_copy[0]["misc"]

        if "prediction_class" in filtered_res_dict and len(detection_incidentflag["prediction_class"]) > 0:
            #print("====updating cache======")
            self.set_cache(detection_incidentflag, cachedict)
        #print("=======Crowd Calculation Done=======")
        logger.info(f"Template Crowd:completed: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        print(f"Template Crowd:completed: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        

        return detection_data, incident_dict, self.expected_class, masked_image, misc_data
