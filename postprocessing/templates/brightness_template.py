from src.common_template import Template
from src.incidents import IncidentExtract
from src.cache import Caching
class BrightnessTemplate(Template,IncidentExtract,Caching):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame,incidents,usecase_id,rcon=None):
        print("====Initializing crowd=====")
        self.frame=image
        self.allsteps=steps
        self.incidents=incidents
        self.rcon=rcon
        self.usecase_id=usecase_id
        Template.__init__(self,image,image_name,camera_id,image_time,steps,frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self,self.rcon)
            print("====Caching INitilaize done")
            data=self.getbykey('brightness',self.camera_id,self.usecase_id)
            if data is None:
                self.initialize_cache()
    def initialize_cache(self):
        cachedict={}
        cachedict["detections"]=[]
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
        self.setbykey("brightness",self.camera_id,self.usecase_id,cachedict)
        
    def process_data(self):
        print("==============Data==========")
        filtered_res_dict={}
        
        
        filtered_res_dict=self.process_steps()
        print("====Process called=======")
        print(filtered_res_dict)
        cachedict=self.getbykey("brightness",self.camera_id,self.usecase_id)
        IncidentExtract.__init__(self,filtered_res_dict,self.incidents,self.allsteps)
        incident_dict,detected_output=self.process_incident()
        print("=========incident dict======")
        print(incident_dict)
        return filtered_res_dict["misc"], incident_dict,self.expected_class, None




