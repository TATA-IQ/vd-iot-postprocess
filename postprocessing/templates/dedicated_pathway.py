from src.common_template import Template
from src.incidents import IncidentExtract
class DedicatedPathway(Template,Caching,IncidentExtract):
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
    
    def ddp_postprocessing(self,filtered_res_dict):
        detected_list_ovrlap=[]
        
        if len(filtered_res_dict)>0:
            for detclass in detectionres:
                xmin_l, ymin_l, xmax_l, ymax_l = int(detclass['xmin']), int(detclass['ymax']) - int(0.1*(int(detclass['ymax'])-int(detclass['ymin']))), int(detclass['xmax']), int(detclass['ymax'])
                leg_area = np.array([[xmin_l,ymin_l], [xmin_l,ymax_l], [xmax_l, ymax_l], [xmax_l,ymin_l]])
                image_new = np.zeros([image.shape[0],image.shape[1],1],dtype=np.uint8)
                image_new = cv2.fillPoly(image_new, pts =[leg_area], color=(255,255,255))
                img_final = image_new*mask
                count = np.count_nonzero(img_final>0)
                count_pc = 100*count/((xmax_l-xmin_l)*(ymax_l-ymin_l))
                detclass["in_pathway"]=count_pc
                detected_list_ovrlap.append(detclass)
        return detected_list_ovrlap, img_final
            


    
    def process_data(self):
        print("==============Data==========")
        
        filtered_res_dict=self.process_steps()
        print("====Process called=======")
        print(filtered_res_dict)
        self.ddp_postprocessing(filtered_res_dict)





        IncidentExtract.__init__(self,filtered_res_dict,self.incidents,self.allsteps)
        incident_dict=self.process_incident()
        print("=========incident dict======")
        print(incident_dict)
        return filtered_res_dict, incident_dict



