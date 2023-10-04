class PostProcessing():
    def __init__(self,current_detection,old_detection):
        self.current_detection=current_detection
        self.old_detection=old_detection
    
    def get_common(self,ids):
        commonids=[]
        for id_ in ids:
            commonids.extend(list(filter(lambda x:x["id"]==id_,self.current_detection)))
        return commonids
     
     def get_uncommon(self,ids):
        uncommonids=[]
        for id_ in ids:
            uncommonids.extend(list(filter(lambda x:x["id"]==id_,self.current_detection)))
        return uncommonids


    def overlap(self,Xmin, Ymin, Xmax, Ymax, Xmin1, Ymin1, Xmax1, Ymax1):
        if(Xmin>Xmax1 or Xmin1>Xmax or Ymin>Ymax1 or Ymin1>Ymax):
            ov=0
        else:
            ov= (max(Xmin, Xmin1) - min(Xmax, Xmax1)) *  (max(Ymin, Ymin1) -  min(Ymax, Ymax1))
        return round(100*ov/((Xmax1-Xmin1)*(Ymax1-Ymin1)),1)
    
    def filter_data_by_id(self):
        old_detection=[]
        var=[old_detection.extend(i) for i in self.old_detection["prediction_class"] ]
        old_id=[i["id"] for i in old_detection]
        new_id=[i["id"] for i in self.current_detection["prediction_class"]]
        
        common_id=list(set(old_id).intersection(set(new_id)))
        uncommon_id=list(set(old_id)^set(new_id))
        return self.get_common(common_id), self.get_uncommon(uncommon_id)
    
    def filter_data_by_overlap(self):
        old_detection=[]
        commonids=[]
        uncommonids=[]
        var=[old_detection.extend(i) for i in self.old_detection["prediction_class"] ]
        for det in self.current_detection:
            for oldet in old_detection:
                ovlp=overlap(self,oldet["xmin"], oldet["ymin"], oldet["xmax"], oldet["ymax"], det["xmin"], det["ymin"], det["xmax"], det["ymax"])
                if ovlp>=80:
                    commonids.append(det)
                    continue
            uncommonids.append(det)
        return commonids, uncommonids
    
    # def remove_from_incident(self):


            



        
