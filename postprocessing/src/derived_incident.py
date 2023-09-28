class DerivedIncident():
    def __init__(self,detected_data,incident_data,step_data,computation_type):
        self.detected_data=detected_data
        self.incident_data=incident_data
        self.step_data=step_data
        self.expected_incident=[]
        self.computation_type=computation_type
    
    
    def brightness_incident(self):
        count=0
        
        misc=[]
        #brightness_incident=[i for i in list(self.incident_data.values()) if i["measurement_unit"]=="lumen" else pass]
        for brtin in self.incident_data.values():
            
            for det in self.detected_data:
                lower_limit=0
                upper_limit=0
                if det["class_name"]=="brightness":
                    tolerence=self.step_data["tolerance"]
                    
                    lower_limit=float(self.step_data["lower_limit"])-((float(tolerence)/100)*float(self.step_data["lower_limit"]))
                    
                    upper_limit=float(self.step_data["upper_limit"])-((float(tolerence)/100)*float(self.step_data["upper_limit"]))
                    
                    
                    value=det["value"]
                    
                    if value<=lower_limit or value>=upper_limit:
                        misc.append({"brightness":value})
                    print(misc,value,lower_limit,upper_limit)
                
                
                self.expected_incident.append([{"id":count,"incident_id":brtin["incident_id"],"coordinate":{"x1":0,"y1":0,"x2":0,"y2":0},"name":brtin["incident_name"],"misc":misc}])
                
        return self.expected_incident
            
    # def crowd_incident(self):
    #     count=0
    #     for det in self.detection:
    #         if det["class_name"]=="head":
    #             count=count+1
        

    def process_computation_incident(self):
        
        if self.computation_type=="brightness":
            
            return self.brightness_incident()

