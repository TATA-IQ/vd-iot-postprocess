from src.common_template import Template
from src.incidents import IncidentExtract
from src.postprocessing_template import PostProcessing
from src.cache import Caching
from src.compute import Computation
class CrowdTemplate(Template,PostProcessing,IncidentExtract,Caching):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame,incidents,usecase_id,tracker=None,rcon=None,mask=None,image_back=None):
        print("====Initializing crowd=====")
        self.frame=image
        self.allsteps=steps
        self.incidents=incidents
        self.usecase_id=usecase_id
        self.tracker=tracker
        self.mask=mask
        self.image_back=image_back
        self.rcon=rcon
        Template.__init__(self,image,image_name,camera_id,image_time,steps,frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self,self.rcon)
            print("====Caching INitilaize done")
            data=self.getbykey('crowd',self.camera_id,self.usecase_id)
            
            if data is None:
                print("===initializnge cache====")
                self.initialize_cache()
                print("====cache initialized====")
    def initialize_cache(self):
        cachedict={}
    
        cachedict["detections"]=[]
        self.setbykey("crowd",self.camera_id,self.usecase_id,cachedict)
        print("======cache initialized====")
    def set_cache(self,currentdata,cachedict):
        if cachedict is not None:
            if len(cachedict["detections"])>10:
                print(len(cachedict))
                for i in range(9,len(cachedict["detections"])):
                    cachedict["detections"].pop()

                
                cachedict["detections"].insert(0,currentdata)
            else:
                cachedict["detections"].insert(0,currentdata)
        else:
            cachedict={}
            cachedict["detections"]=[]
            cachedict["detections"].insert(0,currentdata)
        self.setbykey("crowd",self.camera_id,self.usecase_id,cachedict)
    

    def process_steps(self):
        final_prediction={}
        masked_image=None
        steps_keys=list(map(lambda x: int(x),list(self.steps.keys())))
        steps_keys.sort()
        #print("========steps keys extracted=====")
        for ki in steps_keys:
            
            step=self.steps[str(ki)]
            if step["step_type"]=="model":
                
                
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
            if step["step_type"]=="computation":
                Computation.__init__(self,final_prediction,step,self.frame)
                print("====final prediction before count====")
                print(final_prediction)
                final_prediction=self.count_crowd()
                print("======prediction after count=====")
                print(final_prediction)
        return final_prediction, masked_image
         
        
    def process_data(self):
        detection_data=[]
        detection_incidentflag={}
        print("==============Data==========")
        filtered_res_dict={}
        filtered_res_dict,masked_image=self.process_steps()
        
        print("====Process called=======")
        print(filtered_res_dict)
        cachedict=self.getbykey("crowd",self.camera_id,self.usecase_id)
        print("=====cachedict====")
        print(cachedict)
        if cachedict is None or len(cachedict)==0:
            pass
        else:
            print("======postprocessing called======")
            print(cachedict)
            print(filtered_res_dict)
            PostProcessing.__init__(self,filtered_res_dict,cachedict["detections"])
            filtered_res_dict["prediction_class"],_=self.filter_data_detection()
        print("=======filtering======")
        if "prediction_class" in filtered_res_dict:
            detection_data=filtered_res_dict["prediction_class"]
            IncidentExtract.__init__(self,filtered_res_dict,self.incidents,self.allsteps)
            incident_dict,detection_incidentflag["prediction_class"]=self.process_incident()
        print("=========incident dict======")
        print(incident_dict)
        print("=======detection data====")
        print(len(detection_data))
        if len(detection_incidentflag)>0:
            self.set_cache(detection_incidentflag,cachedict)
        print("=======Crowd Calculation Done=======")
        
        return detection_data, incident_dict, self.expected_class, masked_image


