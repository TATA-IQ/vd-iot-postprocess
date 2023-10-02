from src.common_template import Template
from src.incidents import IncidentExtract
class BrightnessTemplate(Template,IncidentExtract):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame,incidents):
        print("====Initializing crowd=====")
        self.frame=image
        self.allsteps=steps
        self.incidents=incidents
        Template.__init__(self,image,image_name,camera_id,image_time,steps,frame)
    def process_data(self):
        print("==============Data==========")
        
        filtered_res_dict=self.process_steps()
        print("====Process called=======")
        print(filtered_res_dict)
        IncidentExtract.__init__(self,filtered_res_dict,self.incidents,self.allsteps)
        incident_dict=self.process_incident()
        print("=========incident dict======")
        print(incident_dict)
        return filtered_res_dict, incident_dict




