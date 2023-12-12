"""
pop Template
"""
from src.cache import Caching
from src.common_template import Template
from src.compute import Computation
from src.incidents import IncidentExtract
from src.postprocessing_template import PostProcessing


class PersononPhoneTemplate(Template, Caching, IncidentExtract, PostProcessing):
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
        pop Template Initilization
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
        print("====Initializing pop=====")
        self.frame = image
        self.allsteps = steps
        self.incidents = incidents
        self.usecase_id = usecase_id
        self.tracker = tracker
        self.rcon = rcon
        self.mask = mask
        self.image_back = image_back
        Template.__init__(self, image, split_image, image_name, camera_id, image_time, steps, frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self, self.rcon)
            print("====Caching INitilaize done")
            data = self.getbykey("pop", self.camera_id, self.usecase_id)
            if data is None:
                self.initialize_cache()
                incident_cache= self.getbykey("incident_pop", self.camera_id, self.usecase_id)
                if incident_cache is None:
                    self.initialize_incident_cache()

    def initialize_cache(self):
        """
        cache initialization
        """
        cachedict = {}
        cachedict["detections"] = []

        self.setbykey("pop", self.camera_id, self.usecase_id, cachedict)

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
        self.setbykey("pop", self.camera_id, self.usecase_id, cachedict)
    def initialize_incident_cache(self):
        """
        cache initialization incident
        """
        cachedict = {}

        cachedict["incidents"] = []
        self.setbykey("incident_pop", self.camera_id, self.usecase_id, cachedict)
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
        self.setbykey("incident_pop", self.camera_id, self.usecase_id, cachedict)




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

    def process_data(self,logger):
        '''
        Process pop Template
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
        print("==============Data==========")
        filtered_res_dict = {}
        filtered_res_dict["prediction_class"] = []
        all_detections={}
        all_detections["prediction_class"]=[]
        print("=======caleed pop detection=====")
        # self.detection_init(self.detected_class,self.expected_class,self.image_time)
        all_detections, masked_image = self.process_steps()
        print("**********filtered dic******")
        print(filtered_res_dict)

        print("====Process called=======")
        print(filtered_res_dict)
        cachedict = self.getbykey("pop", self.camera_id, self.usecase_id)
        print("=====cachedict====")
        print(cachedict)
        print("*******fil2*********")
        print(filtered_res_dict)
        if cachedict is None or len(cachedict) == 0:
            self.initialize_cache()
            filtered_res_dict=all_detections
        else:
            print("======postprocessing called======")
            print(cachedict)
            print(filtered_res_dict)

            PostProcessing.__init__(self, all_detections, cachedict["detections"])
            filtered_res_dict["prediction_class"], _ = self.filter_data_detection()
        print("=======filtering======")
        if "prediction_class" in filtered_res_dict:
            detection_data = filtered_res_dict["prediction_class"]
            IncidentExtract.__init__(self, filtered_res_dict, self.incidents, self.allsteps)
            incident_dict, detection_incidentflag["prediction_class"] = self.process_incident()
        print("=========incident dict======")
        print(incident_dict)
        print("=======detection data====")
        print(len(detection_data))
        print("*******fil*********")
        print(filtered_res_dict)
        if len(incident_dict)>0:
            print("====len of incident before filter====",len(incident_dict))
            cachedict_incident=self.getbykey("incident_pop", self.camera_id, self.usecase_id)
            incident_dict,current_incidents=self.filter_base_incidents(cachedict_incident,incident_dict)
            
            self.set_cache_incident(cachedict_incident,current_incidents)
            print("====len of incident after filter====",len(incident_dict))
        if "prediction_class" in filtered_res_dict and len(filtered_res_dict["prediction_class"]) > 0:
            self.set_cache(all_detections, cachedict)

        return detection_data, incident_dict, self.expected_class, masked_image
