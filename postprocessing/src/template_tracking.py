from datetime import datetime
from src.tracking import Tracker
import redis
import pickle
from shared_memory_dict import SharedMemoryDict
from threading import Lock
tracking_smd = SharedMemoryDict(name='tracking', size=10000000)
class TemplateTracking():
    def __init__(self,usecase_id,camera_id,grpcclient):
        
        self.usecase_id=usecase_id
        self.camera_id=camera_id
        self.lock=Lock()
        self.grpcclient=grpcclient

    def tracking_load(self):
        
        if "tracker_"+str(self.usecase_id)+"_"+str(self.camera_id) in tracking_smd:
            
            
            tracker_obj= tracking_smd["tracker_"+str(self.usecase_id)+"_"+str(self.camera_id)]
                
        else:
           
            tracker_obj=Tracker()
            
            
        return tracker_obj
    def tracking_save(self,tracker_obj):
        
        tracking_smd["tracker_"+str(self.usecase_id)+"_"+str(self.camera_id)]=tracker_obj
        

    def track(self,frame,detection_output):
        #print("====inside track======")
        tracker_obj=self.tracking_load()
        detections=[]
        list_det=[]
        # print("=====tracker obj=====")
        # print(tracker_obj)
        # print(detection_output)
        for d in detection_output:
            list_det.append([int(d["xmin"]),int(d["ymin"]),int(d["xmax"]),int(d["ymax"]),float(d["score"])])
        # print("======tracker obj=====")
        # print(tracker_obj)
        # print(list_det)

        # print("===updating track====")
        # print(list_det)
        if len(list_det)>0:
            tracker_obj.update(self.usecase_id,self.camera_id,self.grpcclient,frame,list_det)

        print("===track updated===")
        
        print("=========Length of detection",len(detection_output), len(list_det))
        if tracker_obj.tracks is  not None:

            for trk,det in zip(tracker_obj.tracks,detection_output):
                # print("======inside tracker=====")
                # print("===>",trk.__dir__())
                det["id"]=trk.track_id
                detections.append(det)
            self.tracking_save(tracker_obj)
        return detections
