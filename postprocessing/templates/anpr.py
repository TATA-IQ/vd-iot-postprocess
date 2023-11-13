"""
ANPR Template
"""
from src.cache import Caching
from src.common_template import Template
from src.incidents import IncidentExtract
from src.number_plate_template import NumberPlateTemplate
from src.postprocessing_template import PostProcessing


class ANPRTemplate(Template, Caching, IncidentExtract, PostProcessing, NumberPlateTemplate):
    def __init__(
        self,
        image,
        split_image,
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
        self.rcon = rcon
        self.camera_id=camera_id
        self.mask = mask
        self.image_back = image_back
        Template.__init__(self, image,split_image, image_name, camera_id, image_time, steps, frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self, self.rcon)
            print("====Caching INitilaize done")
            data = self.getbykey("anpr", self.camera_id, self.usecase_id)
            if data is None:
                self.initialize_cache()
            incident_cache= self.getbykey("incident_anpr", self.camera_id, self.usecase_id)
            if incident_cache is None:
                self.initialize_incident_cache()

    def initialize_cache(self):
        """
        cache initialization
        """
        cachedict = {}
        cachedict["detections"] = []

        self.setbykey("anpr", self.camera_id, self.usecase_id, cachedict)

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
        self.setbykey("anpr", self.camera_id, self.usecase_id, cachedict)
    def initialize_incident_cache(self):
        """
        cache initialization incident
        """
        cachedict = {}

        cachedict["incidents"] = []
        self.setbykey("incident_anpr", self.camera_id, self.usecase_id, cachedict)
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
        # print("***********")
        # print(cachedict)
        self.setbykey("incident_anpr", self.camera_id, self.usecase_id, cachedict)



    def process_steps(self):
        '''
        Process the steps of usecase id
        returns :
            final_prediction (dict): filtered result based on preprocessing
            masked_image (dict): numpy array image
        '''
        final_prediction = {}
        masked_image = None
        final_prediction["prediction_class"] = []

        steps_keys = list(map(lambda x: int(x), list(self.steps.keys())))
        steps_keys.sort()

        # print("========steps keys extracted=====")
        # change it here after model update
        for ki in steps_keys:
            print("=====step=====")

            step = self.steps[str(ki)]

            if step["step_type"] == "model" and ki == 1:
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
        print("=====Returnong data=====")

        return final_prediction, masked_image

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
        detection_incidentflag = {}
        incident_dict = []
        detection_data = []
        #print("==============Data==========")
        filtered_res_dict = {}
        filtered_res_dict["prediction_class"] = []
        #print("=======caleed ANPR detection=====")
        # self.detection_init(self.detected_class,self.expected_class,self.image_time)
        logger.info(f"Template ANPR: Detection for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        print(f"Template ANPR: Detection for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        
        filtered_res_dict, masked_image = self.process_steps()
        
        #print("======got vehicle data=====")

        # print(filtered_res_dict)
        logger.info(f"Template ANPR:Seperation of vehicle and number plate for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        print(f"Template ANPR:Seperation of vehicle and number plate for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        
        vehicle_detection = list(
            filter(lambda x: x["class_name"] != "numberplate", filtered_res_dict["prediction_class"])
        )
        numberplate_detection = list(
            filter(lambda x: x["class_name"] == "numberplate", filtered_res_dict["prediction_class"])
        )
        # print("=====filteration of np and vehicle done======")
        # print("========lengt of all detection====", len(filtered_res_dict["prediction_class"]))
        # print("length of number plate===>", len(numberplate_detection))
        # print("length of vehicle===>", len(vehicle_detection))
        if len(numberplate_detection) > 0:
            logger.info(f"Template ANPR:Going for numperplate for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
            print(f"Template ANPR:Going for numperplate for image {self.image_name}  for {self.camera_id} and usecase_id {self.usecase_id}")
        
            NumberPlateTemplate.__init__(
                self, self.frame, self.usecase_id, self.camera_id, self.image_time, self.image_name
            )
            filtered_res_dict["prediction_class"] = self.process_np(
                vehicle_detection, numberplate_detection, self.steps
            )
            # print("%" * 50)

        cachedict = self.getbykey("anpr", self.camera_id, self.usecase_id)
        #print("=====cachedict====")
        logger.info(f"Template ANPR:checking cache, len of cache for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        print(f"Template ANPR:checking cache, len of cache for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        if cachedict is None or len(cachedict) == 0:
            self.initialize_cache()
            logger.info(f"Template ANPR:Reinitialized cache, len of cache: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            print(f"Template ANPR:Reinitialized cache, len of cache: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            
        else:
            print("======postprocessing called======")
            # print(cachedict)
            # print(filtered_res_dict)
            logger.info(f"Template ANPR:Postprocessing called: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            print(f"Template ANPR:Postprocessing called: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            PostProcessing.__init__(self, filtered_res_dict, cachedict["detections"])
            filtered_res_dict["prediction_class"], _ = self.filter_data_detection()
            logger.info(f"Template ANPR:Postprocessing Done: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            print(f"Template ANPR:Postprocessing Done: for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        print("=======filtering======")
        if "prediction_class" in filtered_res_dict:
            detection_data = filtered_res_dict["prediction_class"]
            IncidentExtract.__init__(self, filtered_res_dict, self.incidents, self.allsteps)
            incident_dict, detection_incidentflag["prediction_class"] = self.vehicle_incident_anpr()
            logger.info(f"Template ANPR:Incident Extracted: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
            print(f"Template ANPR:Incident Extracted: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        if len(incident_dict)>0:
            print("====len of incident before filter====",len(incident_dict))
            cachedict_incident=self.getbykey("incident_anpr", self.camera_id, self.usecase_id)
            incident_dict,current_incidents=self.filter_base_incidents_vehicle(cachedict_incident,incident_dict)
            
            self.set_cache_incident(cachedict_incident,current_incidents)
            print("====len of incident after filter====",len(incident_dict))

        if len(filtered_res_dict["prediction_class"]) > 0:
            self.set_cache(detection_incidentflag, cachedict)
        logger.info(f"Template ANPR:completed: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        
        print(f"Template ANPR:completed: {len(incident_dict)} for image {self.image_name} for camera_id {self.camera_id} and usecase_id {self.usecase_id}")
        

        return detection_data, incident_dict, self.expected_class, masked_image
