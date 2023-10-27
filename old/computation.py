from numpy.linalg import norm


class ModelComputation():
    def __init__(self,detection_result,expected_class,expected_incident,detected_incident):
        self.detection_result=detection_result
        self.expected_class=expected_class
        self.expected_incident=expected_incident
        self.detected_incident=detected_incident
    
    def lumen(self,frame,computdata):
        frame=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
        brightness=np.average(norm(img, axis=2)) / np.sqrt(3)
        lower_limit= computdata["lower_limit"]
        upper_limit= computdata["upper_limit"]
        tolerence= computdata["tolerence"]
        if tolerence >0 or tolerence<0:
            lower_limit=lower_limit-(int(tolerence)/100)
            upper_limit=upper_limit+(int(tolerence)/100)
        if brightness<lower_limit or brightness>upper_limit:
            if "misc" in self.detected_incident:
                self.detected_incident["misc"].append({"brightness":round(brightness,2)})
        return self.detected_incident

        
    
    def count_incident(self, detected_output,computdata):
        

        
        


        
    
    def vehicle_speed(self):

        pass



