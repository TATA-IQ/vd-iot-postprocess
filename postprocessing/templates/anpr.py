from src.common_template import Template
from src.cache import Caching
from src.postprocessing_template import PostProcessing
from src.incidents import IncidentExtract
from src.number_plate_template import NumberPlateTemplate

class ANPRTemplate(Template,Caching,IncidentExtract,PostProcessing,NumberPlateTemplate):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame,incidents,usecase_id,tracker=None,rcon=None,mask=None,image_back=None):
        print("====Initializing crowd=====")
        self.frame=image
        self.allsteps=steps
        self.incidents=incidents
        self.usecase_id=usecase_id
        self.tracker=tracker
        self.rcon=rcon
        self.mask=mask
        self.image_back=image_back
        Template.__init__(self,image,image_name,camera_id,image_time,steps,frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self,self.rcon)
            print("====Caching INitilaize done")
            data=self.getbykey('anpr',self.camera_id,self.usecase_id)
            if data is None:
                self.initialize_cache()
    def initialize_cache(self):
        cachedict={}
        cachedict["detections"]=[]
        
        self.setbykey('anpr',self.camera_id,self.usecase_id,cachedict)
    
    
    def set_cache(self,currentdata,cachedict):
        if cachedict is not None:
            if len(cachedict["detections"])>9:
                print(len(cachedict))
                for i in range(10,len(cachedict["detections"])):
                    del cachedict["detections"][i]

                
                cachedict["detections"].insert(0,currentdata)
            else:
                cachedict["detections"].insert(0,currentdata)
        else:
            cachedict={}
            cachedict["detections"]=[]
            cachedict["detections"].insert(0,currentdata)
        self.setbykey("anpr",self.camera_id,self.usecase_id,cachedict)
    

    def process_steps(self):
        final_prediction={}
        masked_image=None
        final_prediction["prediction_class"]=[]
        
        steps_keys=list(map(lambda x: int(x),list(self.steps.keys())))
        steps_keys.sort()
        
        #print("========steps keys extracted=====")
        #change it here after model update
        for ki in steps_keys:
            
            print("=====step=====")
            
            step=self.steps[str(ki)]
            
            if step["step_type"]=="model" and ki==1:
                
                
                self.expected_class.extend(list(step["classes"].values()))
                #print("=======inside model===")
                self.model_call(step)
                #print("====inside step model===")
                if len(self.detected_class)>0:
                    self.detection_init(self.detected_class,self.expected_class,self.image_time)
                    
                    filtered_res=self.process_detection()
                    if self.tracker is not None:
                        filtered_res=self.tracker.track(self.image,filtered_res)
                    self.filtered_output.extend(filtered_res)
                    print("=====length of detection===",len(filtered_res))
                    final_prediction["prediction_class"]=self.filtered_output
                if self.mask is not None:
                    final_prediction["prediction_class"],masked_image=self.masked_detection(self.mask,self.image_back, final_prediction["prediction_class"])
                    print("=====masked perdiction=====")
                    print(final_prediction["prediction_class"])
        print("=====Returnong data=====")
            
        return final_prediction, masked_image
    
    
     
    
    def process_data(self):
        detection_incidentflag={}
        incident_dict=[]
        detection_data=[]
        print("==============Data==========")
        filtered_res_dict={}
        filtered_res_dict["prediction_class"]=[]
        print("=======caleed ANPR detection=====")
        #self.detection_init(self.detected_class,self.expected_class,self.image_time)
        filtered_res_dict,masked_image=self.process_steps()
        print("======got vehicle data=====")

        # print(filtered_res_dict)
        
        vehicle_detection=list(filter(lambda x:x["class_name"]!="numberplate",filtered_res_dict["prediction_class"]))
        numberplate_detection=list(filter(lambda x:x["class_name"]=="numberplate",filtered_res_dict["prediction_class"]))
        print("=====filteration of np and vehicle done======")
        print("========lengt of all detection====",len(filtered_res_dict["prediction_class"]))
        print("length of number plate===>",len(numberplate_detection))
        print("length of vehicle===>",len(vehicle_detection))
        if len(numberplate_detection)>0:
            print("#"*50)
            NumberPlateTemplate.__init__(self,self.frame,self.usecase_id,self.camera_id,self.image_time)
            filtered_res_dict["prediction_class"]=self.process_np(vehicle_detection,numberplate_detection,self.steps)
            print("%"*50)
        
        cachedict=self.getbykey("anpr",self.camera_id,self.usecase_id)
        print("=====cachedict====")
        
        if cachedict is None or len(cachedict)==0:
            pass
        else:
            print("======postprocessing called======")
            # print(cachedict)
            # print(filtered_res_dict)
            PostProcessing.__init__(self,filtered_res_dict,cachedict["detections"])
            filtered_res_dict["prediction_class"],_=self.filter_data_detection()
        print("=======filtering======")
        if "prediction_class" in filtered_res_dict:
            detection_data=filtered_res_dict["prediction_class"]
            IncidentExtract.__init__(self,filtered_res_dict,self.incidents,self.allsteps)
            incident_dict,detection_incidentflag["prediction_class"]=self.vehicle_incident()
        print("=========incident dict======")
        
        print("=======detection data====")
        print(detection_data)
        print(len(detection_data))


        if len(filtered_res_dict["prediction_class"])>0:
            self.set_cache(detection_incidentflag,cachedict)
        
        return detection_data, incident_dict, self.expected_class, masked_image
        

