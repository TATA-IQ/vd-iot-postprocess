class IncidentCreate():
    def __init__(self, incidents,detectiondata):
        self.incidents=incidents
        self.detectiondata=detectiondata
    
    
    def process(self):
        incidentkeys=list(self.incidents.keys())
        incident_class=[self.incidents[i]["class_name"] for i in self.incidents]
        incident_name=[self.incidents[i]["incident_name"] for i in self.incidents]
        incidentlist=[]
        incident_id=1
        for dtdata in self.detectiondata:
            incidentdict={}
            if dtdata["class_name"] in incident_class:
                incidentdict["id"]=incident_id
                incidentdict["incident_id"]=str(incidentkeys[incident_class.index(dtdata["class_name"])])
                incidentdict["name"]=incident_name[incident_class.index(dtdata["class_name"])]
                incidentdict["coordinate"]={"x1":dtdata["xmin"],"x2":dtdata["xmax"],"y1":dtdata["ymin"],"y2":dtdata["ymax"]}
                incidentdict["misc"]=[]
                incident_id=incident_id+1
                incidentlist.append(incidentdict)
        return incidentlist
    
    





