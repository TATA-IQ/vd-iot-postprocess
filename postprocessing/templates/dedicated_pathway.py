from src.common_template import Template
from src.incidents import IncidentExtract
from src.postprocessing_template import 
class DedicatedPathway(Template,Caching,IncidentExtract,PostProcessing):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame,incidents,usecase_id,tracker=None,rcon=None):
        print("====Initializing crowd=====")
        self.frame=image
        self.allsteps=steps
        self.tracker=tracker
        self.incidents=incidents
        
        Template.__init__(self,image,image_name,camera_id,image_time,steps,frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self,self.rcon)
            print("====Caching INitilaize done")
            data=self.getbykey('ddp',self.camera_id,self.usecase_id)
            
            if data is None:
                self.initialize_cache()
    def initialize_cache(self):
        
        cachedict={}
        cachedict["unique_id"]=[]
        
        cachedict["image"]=""
        cachedict["detections"]=[]
        print("======caching initialization done====")
        self.setbykey("ddp",self.camera_id,self.usecase_id,cachedict)
        print("=====cache dict saved to cache")
    
    
            

    def process_steps(self):
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
                    self.detection_init()
                    
                    filtered_res=self.process_detection()
                    self.filtered_output.extend(filtered_res)
                    self.final_prediction["prediction_class"]=self.filtered_output
                if self.mask is not None:
                    self.final_prediction["prediction_class"]=self.masked_detection(self.frame,self.mask, filtered_res_dict)

            if step["step_type"]=="computation":
                Computation.__init__(self,self.final_prediction,step,self.frame)
                 self.final_prediction=self.ddp_computation(self.final_prediction)
            
        





    
    def process_data(self):
        print("==============Data==========")
        prexistdata=None
        filtered_res_dict=self.process_steps()
        print("====Process called=======")
        print(filtered_res_dict)
        self.process_steps()
        data=self.getbykey("ddp",self.usecase_id,self.camera_id)
        if data is not None:
            prexistdata=data
            if len(data)>9:
                data[0]=self.final_prediction
            else:
                data.append(self.final_prediction)
        else:
            data=[self.final_prediction]
        self.setbykey("ddp",self.usecase_id,self.camera_id,data)
        IncidentExtract.__init__(self,self.final_prediction,self.incident,self.steps)
        
        #prepare the data to save
        # if prexistdata is not None:
        #     PostProcessing(self.final_prediction,prexistdata)
        #     if self.tracker is not None:
        #         common,uncommon=self.filter_data_by_id()
        #     else:
        #         common,uncommon=self.filter_data_by_overlap()
        # self.final_prediction["prediction_class"]=uncommon
        

    
            



        

        





        IncidentExtract.__init__(self,filtered_res_dict,self.incidents,self.allsteps)
        incident_dict=self.process_incident()
        print("=========incident dict======")
        print(incident_dict)
        return filtered_res_dict, incident_dict



