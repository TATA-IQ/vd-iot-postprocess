from src.common_template import Template
from src.incidents import IncidentExtract

class PPETemplate(Template,Caching,IncidentExtract,PostProcessing):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame,incidents,usecase_id,tracker=None,rcon=None):
        print("====Initializing crowd=====")
        self.frame=image
        self.allsteps=steps
        self.incidents=incidents
        self.usecase_id=usecase_id
        self.tracker=tracker
        self.rcon=rcon
        Template.__init__(self,image,image_name,camera_id,image_time,steps,frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self,self.rcon)
            print("====Caching INitilaize done")
            data=self.getbykey('ppe',self.camera_id,self.usecase_id)
            if data is None:
                self.initialize_cache()
    def initialize_cache(self):
        cachedict={}
        cachedict["detection"]=[]
        cachedict["incident"]=[]
        self.self.getbykey('ppe',self.camera_id,self.usecase_id,cachedict)
    def overlap(self,Xmin, Ymin, Xmax, Ymax, Xmin1, Ymin1, Xmax1, Ymax1):
        if(Xmin>Xmax1 or Xmin1>Xmax or Ymin>Ymax1 or Ymin1>Ymax):
            ov=0
        else:
            ov= (max(Xmin, Xmin1) - min(Xmax, Xmax1)) *  (max(Ymin, Ymin1) -  min(Ymax, Ymax1)); 
        return round(100*ov/((Xmax1-Xmin1)*(Ymax1-Ymin1)),1)

    def check_overlap_classes(self,person_data,data):
        
        for dt in data:
            if dt["class_name"] in self.expected_classes:
                
                overlap=self.overlap(person_data["xmin"],person_data["ymin"],person_data["xmax"],person_data["ymax"],dt["xmin"],dt["ymin"],dt["xmax"],dt["ymax"])
                if overlap>=80:
                    yield dt
    def filter_data(self):
        finalresult=[]
        for dt in self.data:
            if dt["class_name"]=="person" or dt["class_name"]=="human":
                finalresult.append(dt)
                for ovr in self.check_overlap_classes(dt,self.data):
                    finalresult.append(ovr)
                
        return finalresult
    def process_data(self):
        print("==============Data==========")
        
        filtered_res_dict=self.process_steps()
        filtered_res_dict["prediction_class"]=self.filter_data(filtered_res_dict["prediction_class"])

        print("====Process called=======")
        print(filtered_res_dict)
        data=self.getbykey("ppe",self.usecase_id,self.camera_id)
        if data is not None:
            prexistdata=data
            if len(data)>9:
                data[0]=self.final_prediction
            else:
                data.append(self.final_prediction)
        else:
            data=[self.final_prediction]
        self.setbykey("ppe",self.usecase_id,self.camera_id,data)
        #prepare the data to save

        IncidentExtract.__init__(self,self.final_prediction,self.incident,self.steps)
        incident_dict=self.process_incident()
        return filtered_res_dict["prediction_class"], incident_dict

        # if prexistdata is not None:
        #     PostProcessing(self.final_prediction,prexistdata)
        #     if self.tracker is not None:
        #         common,uncommon=self.filter_data_by_id()
        #     else:
        #         common,uncommon=self.filter_data_by_overlap()
        # self.final_prediction["prediction_class"]=uncommon
        
        

        # #IncidentExtract.__init__(self,filtered_res_dict,self.incidents,self.allsteps)
        
        # print("=========incident dict======")
        # print(incident_dict)
        



