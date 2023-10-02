import cv2
import numpy as np
class Computation():
    def __init__(self,detection_dict, steps,frame):
        self.detection_output=detection_dict
        self.steps=steps
        self.frame=frame
    
    def count(self):
        misc=[]
        dictres={}
        print("======self.detection======")
        print(self.detection_output)
        if "prediction_class" in self.detection_output:
            for i in self.detection_output["prediction_class"]:
                print("=======i======",i)
                if i["class_name"] in dictres:
                    dictres[i["class_name"]]=dictres[i["class_name"]]+1
                else:
                    dictres[i["class_name"]]=1
            print("=====dicres====")
            print(dictres)
            for k,v in dictres.items():
                tempdict={}
                tempdict[k]=v
                misc.append(tempdict)
            print("====misc===")
            print(misc)
            print(self.detection_output)
            if "misc" in self.detection_output:
                
                self.detection_output["misc"].extend(misc)
            else:
                self.detection_output["misc"]=misc
        
                
    
    def brightness(self):
        frame=cv2.cvtColor(self.frame,cv2.COLOR_BGR2HSV)
        h,s,v=cv2.split(frame)
        
        brightness=np.mean(v)
        misc=[]
        misc.append({"brightness":brightness})
        if "misc" in self.detection_output:
                
                self.detection_output["misc"].extend(misc)
        else:
            self.detection_output["misc"]=misc
    
    def svd(self):
        pass
    
    def process_computation(self):
        compute_name=self.steps["computation_name"]
        if compute_name=="count":
            self.count()
        if compute_name=="brightness":
            self.brightness()
        if compute_name=="svd":
            self.svd()
        return self.detection_output

        


