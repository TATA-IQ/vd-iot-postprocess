from src.common_template import Template
class NumberPlateTemplate(Template):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame,incidents):
        print("====Initializing crowd=====")
        self.frame=image
        self.allsteps=steps
        self.incidents=incidents
        Template.__init__(self,image,image_name,camera_id,image_time,steps,frame)
    
    

    def process_steps(self):
        print("=====template step proces=====")
        steps_keys=list(map(lambda x: int(x),list(self.steps.keys())))
        steps_keys.sort()
        print("========steps keys extracted=====")
        for ki in steps_keys:
            
            step=self.steps[str(ki)]
            if step["step_type"]=="model" :
                
                
                self.expected_class.extend(list(step["classes"].values()))
                print("=======inside model===")
                self.model_call(step)
                #print("====inside step model===")
                if len(self.detected_class)>0:
                    DetectionProcess.__init__(self,self.detected_class,self.expected_class)
                    filtered_res=self.process_detection()
                    self.filtered_output.extend(filtered_res)
                    self.final_prediction["prediction_class"]=self.filtered_output

            

            
