import cv2
import numpy as np
class Computation():
    def __init__(self,detection_dict, steps,frame):
        self.detection_output=detection_dict
        self.steps=steps
        self.frame=frame
    
    def count_crowd(self):
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
                tempdict["data"]=v
                tempdict["text"]=k
                misc.append(tempdict)
            print("====misc===")
            print(misc)
            print(self.detection_output)
            if "misc" in self.detection_output:
                
                self.detection_output["misc"].extend(misc)
            else:
                self.detection_output["misc"]=misc
        
        return self.detection_output
                
    
    def brightness(self):
        frame=cv2.cvtColor(self.frame,cv2.COLOR_BGR2HSV)
        h,s,v=cv2.split(frame)
        
        brightness=np.mean(v)
        misc=[]
        misc.append({"data":brightness,"text":"brightness"})
        if "misc" in self.detection_output:
                
                self.detection_output["misc"].extend(misc)
        else:
            self.detection_output["misc"]=misc
    
    def svd(self):


        pass

    def ddp_computation(self):
        misc=[]
        
        print("======self.detection======")
        print(self.detection_output)
        if "prediction_class" in self.detection_output:
            for i in self.detection_output["prediction_class"]:
                dictres={}
                print("=======i======",i)
                dictres["data"]=i[i["class_name"]]
                dictres["text"]="overlap"
                #dictres["id"]=i["id"]
                misc.append(dictres)
            # tempdict={}
                
            # for k,v in dictres.items():
            #     tempdict[k]=v
                
                
            
            if "misc" in self.detection_output:
                
                self.detection_output["misc"].extend(misc)
            else:
                self.detection_output["misc"]=misc
        return self.detection_output
    
    def speed_computation(self):
        misc=[]
        if "prediction_class" in self.detection_output:
            for i in self.detection_output["prediction_class"]:
                listres=[]
                if "speed" in i:
                    dictres={}
                    dictres["data"]=i["speed"]
                    dictres["text"]="speed"
                    dictres2["id"]=i["id"]
                    misc.append(dictres)
                if i["class_name"] in i:
                    dictres2={}
                    dictres2["data"]=i[i["class_name"]]
                    dictres2["text"]="numberplate"
                    dictres2["id"]=i["id"]
                    misc.append(dictres2)
        
    
        if "misc" in self.detection_output:
            
            self.detection_output["misc"].extend(misc)
        else:
            self.detection_output["misc"]=misc
        
        return self.detection_output
        






    
    def process_computation(self):
        compute_name=self.steps["computation_name"]
        if compute_name=="count":
            self.count()
        if compute_name=="brightness":
            self.brightness()
        if compute_name=="svd":
            self.svd()
        return self.detection_output

        


