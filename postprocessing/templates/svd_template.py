class SpeedDetection():
    def __init__(self,usecase_id,cam_id,detected_output):
        self.detected_output=detected_output
        self.usecase_id=usecase_id
        self.cam_id=cam_id
        self.unique_ids=[]
        self.time_dict=[]
        self.x1,self.y1, self.x2,self.y2={},{},{},{}
    
    def calculate_speed(self):
        #load id
        track_ids=[int(i["id"]) for i in self.detected_output]
        class_data=[int(i["class_id"]) for i in self.detected_output]
        boxes=[[i["xmin"],i["ymin"],i["xmax"],i["ymax"] for i in self.detected_output]]
        id_list=[]
        for box, clsid, trckid in zip(boxes,class_data,track_ids):
            if self.unique_ids is not None and trckid in self.unique_ids:
                if trckid not in self.y2:






        