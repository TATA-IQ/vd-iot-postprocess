class PostProcessing():
    def __init__(self,current_detection,old_detection):
        self.current_detection=current_detection
        self.old_detection=old_detection
    
    

    def overlap(self,Xmin, Ymin, Xmax, Ymax, Xmin1, Ymin1, Xmax1, Ymax1):
        if(Xmin>Xmax1 or Xmin1>Xmax or Ymin>Ymax1 or Ymin1>Ymax):
            ov=0
        else:
            ov= (max(Xmin, Xmin1) - min(Xmax, Xmax1)) *  (max(Ymin, Ymin1) -  min(Ymax, Ymax1))
        return round(100*ov/((Xmax1-Xmin1)*(Ymax1-Ymin1)),1)
    
    def filter_data_detection(self):
        print("======filtering Started======")
        uncommondict=[]
        commondict=[]
        varolddata=[]
        if len(self.current_detection)>0:
            newdata=[i for i in self.current_detection["prediction_class"]]
        else:
            return [],[]
        if len(self.old_detection)>0:
            [varolddata.extend(i["prediction_class"]) for i in self.old_detection ]
        else:
            return newdata,newdata
        
        for det in newdata:
            for oldet in varolddata:
                if det["id"] is not None:
                    if det["id"] == oldet["id"] and oldet["incident_status"]==True:
                        commondict.append(det)
                        continue
                    

                else:
                    overlap=self.overlap(oldet["xmin"], oldet["ymin"], oldet["xmax"], oldet["ymax"], det["xmin"], det["ymin"], det["xmax"], det["ymax"])
                    
                    if overlap>80:
                        commondict.append(det)
                        continue
                   
            uncommondict.append(det)
        print("Length of common dict===>",len(commondict))
        print("Length of uncommon dict===>",len(uncommondict))
        return uncommondict, commondict
    def filter_misc_incident(self,prev_misc_data,current_misc_data):
        misc_data=[]
        prev_data=[]
        _=[prev_data.extend(i["misc"]) in prev_misc_data]
        for cmd in current_misc_data:
            for pmd in prev_data:
                if cmd["text"]==pmd["text"]:
                    if cmd["data"]==pmd["data"]:
                        break;
            misc_data.append(cmd)
        return misc_data


    
    # def filter_data_comp(self):
    #     current_detection=[i for i in self.current_detection["misc"]]
    #     old_detection=[i for i in self.old_detection]
    #     for ct in current_detection:
    #         for oldct in old_detection :
                




    # def filter_data_values(self):
    #     cleandict=[]
    #     newdata=[i for i in self.old_detection["misc"]]
    #     varolddata=[old_detection.extend(i) for i in self.old_detection["misc"] ]
    #     for oldet in varolddata:
    #         for det in newdata:
    #             if det["id"] is not None:
    #                 if det["id"] == oldet["id"] and oldet["incident_status"]==True:
    #                     continue
    #                 else:
    #                     cleandict.append(det)
    #             else:
    #                 overlap=self.overlapoverlap(self,oldet["xmin"], oldet["ymin"], oldet["xmax"], oldet["ymax"], det["xmin"], det["ymin"], det["xmax"], det["ymax"])
    #                 if overlap>80:
    #                     continue
    #                 else:
    #                     cleandict.append(det)
    #     return cleandict

    