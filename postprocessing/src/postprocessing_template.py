import collections
import numpy as np
class PostProcessing:
    def __init__(self, current_detection, old_detection):
        self.current_detection = current_detection
        self.old_detection = old_detection

    def overlap(self, Xmin, Ymin, Xmax, Ymax, Xmin1, Ymin1, Xmax1, Ymax1):
        if Xmin > Xmax1 or Xmin1 > Xmax or Ymin > Ymax1 or Ymin1 > Ymax:
            ov = 0
        else:
            ov = (max(Xmin, Xmin1) - min(Xmax, Xmax1)) * (max(Ymin, Ymin1) - min(Ymax, Ymax1))
        return round(100 * ov / ((Xmax1 - Xmin1) * (Ymax1 - Ymin1)), 1)

    def filter_data_detection(self):
        print("======filtering Started======")
        uncommondict = []
        commondict = []
        varolddata = []
        if len(self.current_detection) > 0:
            newdata = [i for i in self.current_detection["prediction_class"]]
        else:
            return [], []
        if len(self.old_detection) > 0:
            [varolddata.extend(i["prediction_class"]) for i in self.old_detection]
        else:
            return newdata, newdata
        allindex=[]
        commonindex=[]
        print("====filter loop=====")
        for idx,det in enumerate(newdata):
            allindex.append(idx)
            for oldet in varolddata:
                if det["id"] is not None:
                    if det["id"] == oldet["id"]: #and oldet["incident_status"] == True:
                        commondict.append(det)
                        commonindex.append(idx)
                        

                else:
                    overlap = self.overlap(
                        oldet["xmin"],
                        oldet["ymin"],
                        oldet["xmax"],
                        oldet["ymax"],
                        det["xmin"],
                        det["ymin"],
                        det["xmax"],
                        det["ymax"],
                    )

                    if overlap > 80:
                        commondict.append(det)
                        commonindex.append(idx)
                        continue

            uncommondict.append(det)
            commonindex.append(idx)
        print("====looping end=====")
        print("=========len current detection====",len(newdata))
        print("=========len old detection====",len(varolddata))
        print("==========leng of old dict=======",len(self.old_detection))
        freqcount=collections.Counter(commonindex)
        print("======frequency count======",commonindex)
        print(freqcount)
        freq_per=list(map(lambda x: {x:round((freqcount[x]/len(commonindex))*100,2)},freqcount))
        print("======freq per=====",freq_per)
        filterecommon_indx=list(filter(lambda x: x[list(x.keys())[0]]>10,freq_per))
        print("=======filter=====",filterecommon_indx)
        commonindex=list(map(lambda x: list(x.keys())[0],filterecommon_indx))
        commondict=[self.current_detection["prediction_class"][i] for i in commonindex]
        #uncommondict=[self.current_detection[i] for i in commonindex]
        print("Length of common dict===>", len(commondict))
        print("Length of uncommon dict===>", len(self.current_detection["prediction_class"]))
        return  commondict, None

    def filter_misc_incidents(self,cachedict_incident,current_incidents):
        #cachedict_incident = self.getbykey("incident_crowd", self.camera_id, self.usecase_id)
        old_incident_list=sum(cachedict_incident["incidents"],[])
        # [old_incident_list.extend(i["misc"]) for i in cachedict_incident]
        inclist=[]
        indxlist=[]
        commonindxlist=[]
        print("=====incident cache====",cachedict_incident)
        if len(cachedict_incident["incidents"] )>0:
            for idx,ctd in enumerate(current_incidents):
                indxlist.append(idx)
                for cachinc in old_incident_list:
                    cach_misc=cachinc["misc"]
                    ctd_misc=ctd["misc"]
                    for misc_ctd in ctd_misc:
                        for misc_cach in cach_misc:
                            if misc_cach["text"]==misc_ctd["text"] and misc_cach["data"]==misc_ctd["data"]:
                                commonindxlist.append(idx)
                            
        
            
        else:
            print("======Returning current incidents======")
            inclist= current_incidents
        if len(commonindxlist)>0:
            print("========common index list====",commonindxlist)
            indxlist=list(set(indxlist)^set(commonindxlist))
            print("=====lsit to report======",indxlist)
            indxlist=list(set(indxlist))
            inclist=[current_incidents[i] for i in indxlist]

        #self.set_cache_incident(cachedict_incident,current_incidents)
        return inclist,current_incidents
    
    def filter_base_incidents(self,cachedict_incident,current_incidents):
        #cachedict_incident = self.getbykey("incident_crowd", self.camera_id, self.usecase_id)
        old_incident_list=sum(cachedict_incident["incidents"],[])
        # [old_incident_list.extend(i["misc"]) for i in cachedict_incident]
        inclist=[]
        indxlist=[]
        commonindxlist=[]
        print("=====incident cache====",cachedict_incident)
        if len(cachedict_incident["incidents"] )>0:
            for idx,ctd in enumerate(current_incidents):
                indxlist.append(idx)
                for cachinc in old_incident_list:
                    overlap = self.overlap(cachinc["coordinate"]["x1"],cachinc["coordinate"]["y1"],cachinc["coordinate"]["x2"],cachinc["coordinate"]["y2"],ctd["coordinate"]["x1"],ctd["coordinate"]["y1"],ctd["coordinate"]["x2"],ctd["coordinate"]["y2"])
                    if cachinc["track_id"]==ctd["track_id"]:
                        commonindxlist.append(idx)
                    if overlap>80:
                        commonindxlist.append(idx)

            
        else:
            print("======Returning current incidents======")
            inclist= current_incidents
        if len(commonindxlist)>0:
            print("========common index list====",commonindxlist)
            indxlist=list(set(indxlist)^set(commonindxlist))
            print("=====lsit to report======",indxlist)
            indxlist=list(set(indxlist))
            inclist=[current_incidents[i] for i in indxlist]

        #self.set_cache_incident(cachedict_incident,current_incidents)
        return inclist,current_incidents
    
    
    def filter_base_incidents_vehicle(self,cachedict_incident,current_incidents):
        #cachedict_incident = self.getbykey("incident_crowd", self.camera_id, self.usecase_id)
        old_incident_list=sum(cachedict_incident["incidents"],[])
        # [old_incident_list.extend(i["misc"]) for i in cachedict_incident]
        inclist=[]
        indxlist=[]
        commonindxlist=[]
        print("**********************************")
        print("=====incident cache====",cachedict_incident)
        if len(cachedict_incident["incidents"] )>0:
            for idx,ctd in enumerate(current_incidents):
                indxlist.append(idx)
                for cachinc in old_incident_list:
                    cach_misc=cachinc["misc"]
                    ctd_misc=ctd["misc"]
                    print(cach_misc)
                    print(ctd_misc)
                    for misc_ctd in ctd_misc:
                        for misc_cach in cach_misc:
                            if misc_cach["text"]==misc_ctd["text"] and misc_cach["data"]==misc_ctd["data"]:
                                commonindxlist.append(idx)

                    
                     

            
        else:
            print("======Returning current incidents======")
            inclist= current_incidents
        if len(commonindxlist)>0:
            print("========common index list====",commonindxlist)
            print("===index list====",indxlist)
            indxlist=list(set(indxlist)^set(commonindxlist))
            print("=====lsit to report======",indxlist)
            indxlist=list(set(indxlist))
            inclist=[current_incidents[i] for i in indxlist]
        print(commonindxlist)

        #self.set_cache_incident(cachedict_incident,current_incidents)
        return inclist,current_incidents