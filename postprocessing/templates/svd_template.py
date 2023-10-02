from src.common_template import Template
from src.incidents import IncidentExtract
from src.template_tracking import TemplateTracking
import cv2
from shared_memory_dict import SharedMemoryDict
from threading import Lock
from src.cache import Caching
svd_smd = SharedMemoryDict(name='svd', size=10000000)


class SVDTemplate(Template,Caching):
    def __init__(self,image,image_name,camera_id,image_time,steps,frame,incidents,usecase_id,image_time,tracker=None,rcon=None):
        print("====Initializing SVD=====")
        self.rcon=rcon
        self.usecase_id=usecase_id
        self.frame=frame
        self.allsteps=steps
        self.incidents=incidents
        self.tracker=tracker
        self.image=image
        self.rcon=rcon
        self.image_time=image_time
        self.cache_data=None
        Template.__init__(self,image,image_name,camera_id,image_time,steps,frame)
        if rcon is not None:
            Caching.__init__(rcon)
            self.cache_data=self.getbykey(self.usecase_id,self.camera_id)
    

    def speed_cal(self, T1, T2, T3):
        print("======Calling Speed Calculation======")
        time_diff_1 = T2 - T1
        time_diff_2 = T3 - T2
        time_diff = time_diff_1 + time_diff_2
        if time_diff != 0:
            distance = 20  # meters
            speed_res = distance / time_diff
            speed_res = round(speed_res * 3.6, 2)
        return speed_res
            
    def line(self, frame,frame_width,frame_height):
        y_1 = max(0, min(frame_height - 1, self.y_l1))
        y_3 = max(0, min(frame_height - 1, self.y_l2))
        # line between line 1 and line 3
        y_2 = int((self.y_l1 + self.y_l2)//2)
        y_2 = max(0, min(frame_height - 1, y_2))
        cv2.line(frame, (0, y_1), (frame_width, y_1),  color=(0, 255, 0), thickness=2)
        cv2.line(frame, (0, y_2), (frame_width, y_2),  color=(0, 255, 0), thickness=2)
        cv2.line(frame, (0, y_3), (frame_width, y_3),  color=(0, 255, 0), thickness=2)
        line_one_ = [0, y_1, frame_width, y_1]
        line_two_ = [0, y_2, frame_width, y_2]
        line_three_ = [0, y_3, frame_width, y_3]
        list_lines=[]
        list_lines.append(line_one_)
        list_lines.append(line_two_)
        list_lines.append(line_three_)
        frame=self.draw_line(frame,frame_width,list_lines)
        return frame,list_lines
            
    def intersecting_lines_down(self, obj_id,vehicle_ymax,line_list,ctime):
        # print('time dict :', cachedict["time_dict"][obj_id])
        temp_line_list=list(reversed(line_list[1:-1]))
        for idx,li in enumerate(temp_line_list):
            if vehicle_ymax<=li[1]:
                cachedict["time_dict"][obj_id]["time"]['t'+str(idx+2)]=ctime
                cachedict["time_dict"][obj_id]["vehicle_coords"].append([cachedict["time_dict"][obj_id]["coords"]["xmin"],cachedict["time_dict"][obj_id]["coords"]["ymin"],cachedict["time_dict"][obj_id]["coords"]["xmax"],cachedict["time_dict"][obj_id]["coords"]["ymax"]])
                        
    def intersecting_lines_up(self, obj_id,vehicle_ymax,line_list,ctime):
        temp_line_list=line_list[1:-1]
        for idx,li in enumerate(temp_line_list):
            if vehicle_ymax<=li[1]:
                cachedict["time_dict"][obj_id]["time"]['t'+str(idx+2)]=ctime
                cachedict["time_dict"][obj_id]["vehicle_coords"].append([cachedict["time_dict"][obj_id]["coords"]["xmin"],cachedict["time_dict"][obj_id]["coords"]["ymin"],cachedict["time_dict"][obj_id]["coords"]["xmax"],cachedict["time_dict"][obj_id]["coords"]["ymax"]])

    
    def process_steps(self):
        print("=====template step proces=====")
        steps_keys=list(map(lambda x: int(x),list(self.steps.keys())))
        steps_keys.sort()
        print("========steps keys extracted=====")
        for ki in steps_keys:
            if ki==1:
                step=self.steps[str(ki)]

                if step["step_type"]=="model":
                    
                    
                    self.expected_class.extend(list(step["classes"].values()))
                    print("=======inside model===")
                    self.model_call(step)
                    #print("====inside step model===")
                    print("=====deected class===")
                    print(self.detected_class)

                    if len(self.detected_class)>0:
                        self.detection_init()
                        #DetectionProcess.__init__(self,self.detected_class,self.expected_class)
                        filtered_res=self.process_detection()
                        self.filtered_output.extend(filtered_res)
                        print("=====pred class==")
                        self.final_prediction["prediction_class"]=self.filtered_output
            return self.final_prediction
    
    def process_data(self):
        print("==============SVD==========")
        filtered_res_dict=[]
        self.process_steps()
        if "prediction_class" in self.final_prediction:
            filtered_res_dict=self.final_prediction["prediction_class"]
        
        if self.tracker is not None:
            filtered_res_dict=self.tracker.track(self.image,filtered_res_dict)
        #=========check for up or down========
        if len(filtered_res_dict)>0
            frame,detectlist=self.svd_calculation(filtered_res_dict)
            print("=======speed======")
            print(detectlist)
            cv2.imwrite("input/"+self.image_name,self.frame)
        #TemplateTracking()
        # print("=========incident dict======")
        # print(incident_dict)
        # return filtered_res_dict, incident_dict
    def initialize_cache(self):
        cachedict={}
        cachedict["unique_id"]=[]
        cachedict["unique_id_direction"]=[]
        cachedict["object_dict"]={}
        cachedict["time_dict"]={}

        return cachedict


    def svd_calculation(self,filtered_res_dict):
        trackids=[i["id"] for i in filtered_res_dict]
        classidlist=[i["class_id"] for i in filtered_res_dict]
        classnamelist=[i["class_id"] for i in filtered_res_dict]
        detectlist=[i for i in detefiltered_res_dictctionres]
        vehicle_speed=0
        h,w,c=self.frame.shape
        frame=line_list=self.line(self.frame,w,h)
        id_list=[]
        if self.cache_data is  None:
            cachedict=self.initialize_cache()
            self.setbykey(self.usecase_id,self.camera_id,cachedict)
        else:
            cachedict=self.setbykey(self.usecase_id,self.camera_id)
            for idx,id_ in enumerate(trackids):
                if id_ in cachedict["unique_id"]:
                    id_list.append([id_,(detectlist[idx]['xmin'],detectlist[idx]['ymin'],detectlist[idx]['xmax'],detectlist[idx]['ymax'])])
                elif classnamelist[idx].lower()!="np" or  classnamelist[idx].lower()!="numberplate": #all classe by default except numberplate
                    cachedict["unique_id"].append(id_)
                    detectlist[idx]["direction"]=self.check_up_down(line_list[0][1],line_list[2][1],detectlist[idx]["ymax"])
                    detectlist[idx]["state"]=False
                    cachedict["unique_id_direction"].append([id_,detectlist[idx]])
                    if id_ not in cachedict["time_dict"]:
                                cachedict["time_dict"][id_]={'t1': None, 't2': None,  't3':None, 'x1': None,'y1': None,'x2': None,'y2': None, 'speed': None, 'dir': None}
                det = detectlist[idx]
                if len(cachedict["unique_id_direction"])>0:
                    objects_to_remove=[]
                    for j in range(0, len(self.unique_id_direction)):
                            if cachedict["unique_id_direction"][j][0] in ids and cachedict["unique_id_direction"][j][1]["direction"]=="down":
                                obj_id = cachedict["unique_id_direction"][j][0]
                                for id_ , box_ in id_list:
                                    if id_==obj_id:
                                        cachedict["time_dict"][obj_id]['x1'],cachedict["time_dict"][obj_id]['y1'],cachedict["time_dict"][obj_id]['x2'],cachedict["time_dict"][obj_id]['y2'] = box_
                                
                                if cachedict["time_dict"][obj_id]['y2'] is not None and cachedict["time_dict"][obj_id]['y2']<=line_list[2][1]:
                                    if cachedict["time_dict"][obj_id]['t1'] is None:
                                        cachedict["time_dict"][obj_id]['t1']=self.image_time                       
                                    if cachedict["time_dict"][obj_id]['y2'] > line_list[1][1]:
                                        if cachedict["time_dict"][obj_id]['t2'] is None:
                                            cachedict["time_dict"][obj_id]['t2'] = self.image_time
                                    if cachedict["time_dict"][obj_id]['y2'] > line_list[0][1]:
                                        if cachedict["time_dict"][obj_id]['t3'] is None:
                                            cachedict["time_dict"][obj_id]['t3'] = self.image_time
                                if cachedict["time_dict"][obj_id]['t1'] is not None and cachedict["time_dict"][obj_id]['t2'] is not None and cachedict["time_dict"][obj_id]['t3'] is not None:
                                    try:    
                                        print('::::::processing for down ids:::::')
                                        vehicle_speed = self.speed_cal(cachedict["time_dict"][obj_id]['t1'], cachedict["time_dict"][obj_id]['t2'], cachedict["time_dict"][obj_id]['t3'])
                                        print('speed ::',vehicle_speed)
                                        cachedict["time_dict"][obj_id]['speed'] = vehicle_speed
                                        print("Object ID:", obj_id, "Speed:", vehicle_speed, 'kmph')
                                        print('time dict up :', cachedict["time_dict"])
                                        detectlist[idx]["speed"]=vehicle_speed
                                    except:
                                        pass
                            if cachedict["unique_id_direction"][j][0] in ids and cachedict["unique_id_direction"][j][1]["direction"]=="up":
                                obj_id = cachedict["unique_id_direction"][j][0]
                                for id_ , box_ in id_list:
                                    if id_==obj_id:
                                        cachedict["time_dict"][obj_id]['x1'],cachedict["time_dict"][obj_id]['y1'],cachedict["time_dict"][obj_id]['x2'],cachedict["time_dict"][obj_id]['y2'] = box_
                                # print('id:',obj_id, 'y2 :', cachedict["time_dict"][obj_id]['y2'], 'line1:', line_list[0][1], 'line2:', line_list[1][1], 'line3:', line_list[2][1])
                                if cachedict["time_dict"][obj_id]['y2'] is not None and cachedict["time_dict"][obj_id]['y2']>=line_list[0][1]:
                                    if cachedict["time_dict"][obj_id]['t1'] is None:
                                        cachedict["time_dict"][obj_id]['t1']=ctime                       
                                    if cachedict["time_dict"][obj_id]['y2'] > line_list[1][1]:
                                        if cachedict["time_dict"][obj_id]['t2'] is None:
                                            cachedict["time_dict"][obj_id]['t2'] = ctime
                                    if cachedict["time_dict"][obj_id]['y2'] > line_list[2][1]:
                                        if cachedict["time_dict"][obj_id]['t3'] is None:
                                            cachedict["time_dict"][obj_id]['t3'] = ctime
                                    # print('time dict up :', cachedict["time_dict"])
                                if cachedict["time_dict"][obj_id]['t1'] is not None and cachedict["time_dict"][obj_id]['t2'] is not None and cachedict["time_dict"][obj_id]['t3'] is not None:
                                    try:    
                                        print('::::::processing for down ids:::::')
                                        vehicle_speed = self.speed_cal(cachedict["time_dict"][obj_id]['t1'], cachedict["time_dict"][obj_id]['t2'], cachedict["time_dict"][obj_id]['t3'])
                                        print('speed ::',vehicle_speed)
                                        cachedict["time_dict"][obj_id]['speed'] = vehicle_speed
                                        print("Object ID:", obj_id, "Speed:", vehicle_speed, 'kmph')
                                        print('time dict up :', cachedict["time_dict"])
                                        detectlist[idx]["speed"]=vehicle_speed
                                    except:
                                        pass
        self.setbykey(self.usecase_id,self.camera_id,cachedict)
        return frame, detectlist
        

                                        
                                    
                                
                    
                







        for idx,id_ in enumerate(ids):


