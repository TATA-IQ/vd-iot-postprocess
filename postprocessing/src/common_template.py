import requests
from src.model import Model
from src.detectionclass import DetectionProcess
from src.compute import Computation
class Template(Model,DetectionProcess,Computation):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame):
        print("=======Template Initializing======")
        self.image=image
        self.image_name=image_name
        self.camera_id=camera_id
        self.image_time=image_time
        self.steps=steps
        self.frame=frame

        self.detected_class=[]
        self.expected_class=[]
        self.filtered_output=[]
        self.final_prediction={}
        print("=========Template Initialization Done========")
        
    
    def create_request(self,model_type,model_framework):
        requestparams={}
        requestparams["image"]=self.image
        requestparams["image_name"]=self.image_name
        requestparams["camera_id"]=self.camera_id
        requestparams["image_time"]=str(self.image_time)
        requestparams["model_type"]=model_type
        requestparams["model_framework"]=model_framework
        requestparams["model_config"]={'is_track':False,'conf_thres': 0.1,'iou_thres': 0.1,
        'max_det': 300,'agnostic_nms': True,'augment': False}
        return requestparams
    
    def model_call(self,step ):
        
        url=step["model_url"]
        requestparams=self.create_request(step["model_type"],step["model_framework"])
        Model.__init__(self,url,requestparams)
        response=self.api_call()
        if response is not None and response.status_code==200:
            data=response.json()["data"]["result"]
            self.detected_class.extend(data)
                
                

        
    def detection_init(self,detected_class,expected_class,image_time):
        DetectionProcess.__init__(self,detected_class,expected_class,image_time)

    def process_steps(self):
        #print("=====template step proces=====")
        steps_keys=list(map(lambda x: int(x),list(self.steps.keys())))
        steps_keys.sort()
        filtered_output=[]
        final_prediction={}
        #print("========steps keys extracted=====")
        for ki in steps_keys:
            
            step=self.steps[str(ki)]
            if step["step_type"]=="model":
                
                
                self.expected_class.extend(list(step["classes"].values()))
                #print("=======inside model===")
                self.model_call(step)
                #print("====inside step model===")
                if len(self.detected_class)>0:
                    print("=====calling init=======")
                    self.detection_init(self.detected_class,self.expected_class,self.image_time)
                    
                    filtered_res=self.process_detection()
                    filtered_output.extend(filtered_res)
                    final_prediction["prediction_class"]=self.filtered_output

            else:
                Computation.__init__(self,final_prediction,step,self.frame)
                final_prediction=self.process_computation()
                
        return final_prediction







    


    
    