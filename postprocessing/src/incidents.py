class IncidentExtract():
    def __init__(self,detected_output,incidents,steps):
        #print("======Incident======")
        self.detection_output=detected_output
        if "misc" in self.detection_output:
            self.misc=self.detection_output["misc"]
        else:
            self.misc = None
        
        self.incident_id=0
        self.steps=steps
        self.steps_values=list(steps.values())
        print("=====filter steps===")
        #print(self.steps)
        self.derived_steps= list(filter(lambda x: x["step_type"]=="computation",self.steps_values))
        

        self.incident_keys=list(incidents.keys())
        self.incident_values=list(incidents.values())
        print("=====checking incident=====")
        print(self.incident_values)
        self.incident_class_id=[i["class_id"] for i in self.incident_values]
        self.incident_name=[i["incident_name"] for i in self.incident_values]
        self.incident_class=[i["class_name"] for i in self.incident_values]
        self.incident_type_id=[i["incident_type_id"] for i in self.incident_values]
        self.incident_type_name=[i["incident_type_name"] for i in self.incident_values]
        self.incident_list=[]
    
    def base_incident(self):
        if "prediction_class" in self.detection_output:
            for dtdata in self.detection_output["prediction_class"]:
                incidentdict={}
                if dtdata["class_name"] in self.incident_class:
                    incidentdict["id"]=self.incident_id
                    incidentdict["incident_id"]=str(self.incident_class_id[self.incident_class.index(dtdata["class_name"])])
                    incidentdict["name"]=self.incident_name[self.incident_class.index(dtdata["class_name"])]
                    incidentdict["coordinate"]={"x1":dtdata["xmin"],"x2":dtdata["xmax"],"y1":dtdata["ymin"],"y2":dtdata["ymax"]}
                    incidentdict["misc"]=[]
                    self.incident_id=incident_id+1
                    self.incidentlist.append(incidentdict)
        return self.incidentlist
            
    
    
    
   

    def create_derived_incident(self,idx,incident_list):
        incidentdict={}

        incidentdict["id"]=self.incident_id
        incidentdict["incident_id"]=str(self.incident_class_id[idx])
        incidentdict["name"]=self.incident_name[idx]
        incidentdict["coordinate"]={"x1":"","x2":"","y1":"","y2":""}
        incidentdict["misc"]=incident_list
        self.incident_id=self.incident_id+1
        self.incident_list.append(incidentdict)
        


    
    
    def derived_incident(self,idx,step):
        class_name=self.incident_class[idx]
        icident_value=self.incident_values[idx]
        print("======derived incident====")

        upper_limit=float(step["upper_limit"])
        lower_limit=float(step["lower_limit"])
        tolerance=float(step["tolerance"])
        upper_limit=upper_limit+(upper_limit)*tolerance
        lower_limit=lower_limit-(lower_limit)*tolerance
        incident_list=[]
        print("======self misc=====")
        print(self.misc)
        print(class_name)
        if class_name is None:
            for i in self.misc:
                keyslist=list(i.keys())
                print("===keyslist===",keyslist)
                for ki in keyslist:
                    val=i[ki]
                    print("====val===",val,upper_limit,lower_limit)
                    if val>=upper_limit or val<=lower_limit:
                        incident_list.append({ki:val})
        else:
            for i in self.misc:
                keyslist=list(i.keys())
                for ki in keyslist:
                    if ki==class_name:
                        val=i[ki]
                        if val>=upper_limit or val<=lower_limit:
                            incident_list.append({ki:val})
            



        if len(incident_list)>0:
            return self.create_derived_incident(idx,incident_list )
        else:
            return []
    
    def process_incident(self):
        if 1 in self.incident_type_id:
            self.base_incident()
        print("======checking incident type id=====")
        print(self.incident_type_id)
        print(self.derived_steps)
        for idx,inc_id in enumerate(self.incident_type_id):
            print("===i==")
            print(inc_id)
            if int(inc_id)==2:
                for st in self.derived_steps:
                    self.derived_incident(idx,st)
        return self.incident_list







        



            





