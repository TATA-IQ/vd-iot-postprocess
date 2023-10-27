# svd_smd = SharedMemoryDict(name='svd', size=10000000)
from datetime import datetime
from threading import Lock

import cv2
import numpy as np
from shared_memory_dict import SharedMemoryDict
from src.cache import Caching
from src.common_template import Template
from src.compute import Computation
from src.incidents import IncidentExtract
from src.template_tracking import TemplateTracking


class SVDTemplate(Template, Caching, IncidentExtract):
    def __init__(
        self, image, image_name, camera_id, image_time, steps, frame, incidents, usecase_id, tracker=None, rcon=None
    ):
        print("====Initializing SVD=====")
        self.rcon = rcon
        self.usecase_id = usecase_id
        self.frame = frame
        self.allsteps = steps
        self.incidents = incidents
        self.tracker = tracker
        self.image = image
        self.rcon = rcon
        self.image_time = image_time
        self.cache_data = None
        self.y_l1, self.y_l2 = 177, 280
        Template.__init__(self, image, image_name, camera_id, image_time, steps, frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self, self.rcon)
            print("====Caching INitilaize done")
            data = self.getbykey("svd", self.camera_id, self.usecase_id)

            if data is None:
                self.initialize_cache()

    def get_lines_per_pixel(self, y1, y2):
        lines_diff = y2 - y1

        start_cord = []
        end_cord = []
        slope = []
        for i in range(y1, y2, 1):
            start_cord.append(i)
            end_cord.append(i)

        return start_cord, end_cord

    def speedcalc(distlist, timelist):
        uniqpix = list(set(distlist))
        speedlist = []
        print(uniqpix)
        print(timelist)
        for i in range(1, len(uniqpix)):
            td1 = uniqpix[i - 1]
            td2 = uniqpix[i]
            idx1 = distlist.index(td1)
            idx2 = distlist.index(td2)
            tm1 = timelist[idx1]
            tm2 = timelist[idx2]
            print(tm2, tm1)
            print("distance====>", (idx2 - idx1) * 0.07)
            print("time=====>", (tm2 - tm1).total_seconds())
            spd = round((((idx2 - idx1) * 0.07) / (tm2 - tm1).total_seconds()) * (18 / 5), 2)
            speedlist.append(spd)
            print(speedlist)
        return np.mean(speedlist)

    def draw_line(self, frame, frame_width, line_list):
        for lin in line_list:
            cv2.line(frame, (lin[0], lin[1]), (frame_width, lin[-1]), color=(0, 255, 0), thickness=2)
        return frame

    def process_steps(self):
        print("=====template step proces=====")
        steps_keys = list(map(lambda x: int(x), list(self.steps.keys())))
        steps_keys.sort()
        print("========steps keys extracted=====")
        for ki in steps_keys:
            if ki == 1:
                step = self.steps[str(ki)]

                if step["step_type"] == "model":
                    self.expected_class.extend(list(step["classes"].values()))
                    print("=======inside model===")
                    self.model_call(step)
                    # print("====inside step model===")
                    print("=====deected class===")
                    print(self.detected_class)

                    if len(self.detected_class) > 0:
                        self.detection_init(self.detected_class, self.expected_class, self.image_time)
                        # DetectionProcess.__init__(self,self.detected_class,self.expected_class)
                        filtered_res = self.process_detection()
                        self.filtered_output.extend(filtered_res)
                        print("=====pred class==")
                        self.final_prediction["prediction_class"] = self.filtered_output
            return self.final_prediction

    def process_data(self):
        print("==============SVD==========")
        filtered_res_dict = []
        self.process_steps()
        if "prediction_class" in self.final_prediction:
            filtered_res_dict = self.final_prediction["prediction_class"]

        if self.tracker is not None:
            filtered_res_dict = self.tracker.track(self.image, filtered_res_dict)
        # =========check for up or down========
        print("=====tracking done=====")

        if len(filtered_res_dict) > 0:
            print("=======going for svd======")
            frame, detectlist = self.svd_calculation(filtered_res_dict)
            print("=======speed======")
            print(detectlist)
            cv2.imwrite("output/" + self.image_name, frame)
        cv2.imwrite("input/" + self.image_name, self.frame)

    def initialize_cache(self):
        print("=====start caching initialization=====")
        cachedict = {}
        cachedict["unique_id"] = []
        cachedict["unique_id_direction"] = []
        cachedict["object_dict"] = {}
        cachedict["time_dict"] = {}
        cachedict["detections"] = []
        cachedict["road_map"] = []
        cachedict["image_height"] = 640
        cachedict["image_width"] = 640

        print("======caching initialization done====")
        self.setbykey("svd_new", self.camera_id, self.usecase_id, cachedict)
        print("=====cache dict saved to cache")
        # return cachedict

    def update_speed(self, filtered_res_dict, track_id, speed):
        listresult = []
        print("=====updating speed in dict======")
        for i in filtered_res_dict:
            print("=====i=====")
            print(i)
            if int(i["id"]) == int(track_id):
                i["speed"] = speed
            listresult.append(i)
            print("=====speed updated=====")
        print("====updated speed====")
        return listresult

    def svd_calculation(self, filtered_res_dict):
        print("======call for svd=========")
        speed = 0
        trackids = [i["id"] for i in filtered_res_dict]
        classidlist = [i["class_id"] for i in filtered_res_dict]
        classnamelist = [i["class_name"] for i in filtered_res_dict]
        detectlist = [i for i in filtered_res_dict]
        detection_speed_list = None
        vehicle_speed = 0
        h, w, c = self.frame.shape

        cachedict = self.getbykey("svd_new", self.camera_id, self.usecase_id)

        if cachedict is None:
            self.initialize_cache()

        else:
            cachedict = self.getbykey("svd_new", self.camera_id, self.usecase_id)

            cachedict["detections"].extend(filtered_res_dict)

            for idx, id_ in enumerate(trackids):
                print("====idx checking====")
                if id_ in cachedict["unique_id"]:
                    id_list.append(
                        [
                            id_,
                            (
                                detectlist[idx]["xmin"],
                                detectlist[idx]["ymin"],
                                detectlist[idx]["xmax"],
                                detectlist[idx]["ymax"],
                            ),
                        ]
                    )
                    # check for pixel displacement
                    speed = self.pixel_displacement(cachedict["detections"], id_)
                    print("======updatig speed list====")
                    if detection_speed_list is None:
                        detection_speed_list = self.update_speed(detectlist, id_, speed)
                    else:
                        detection_speed_list = self.update_speed(detection_speed_list, id_, speed)
                    print("======speed list updated====")
                    if speed > 1:
                        vehicle_detection = list(filter(lambda x: x["class_name"] != "numberplate", filtered_res_dict))
                        numberplate_detection = list(
                            filter(lambda x: x["class_name"] == "numberplate", filtered_res_dict)
                        )
                        if len(numberplate_detection) > 0:
                            NumberPlateTemplate.__init__(
                                self, self.frame, self.usecase_id, self.camera_id, self.image_time
                            )
                            filtered_res_dict["prediction_class"] = self.process_np(
                                vehicle_detection, numberplate_detection, self.steps
                            )
                            print("%" * 50)

                elif (
                    classnamelist[idx].lower() != "np" or classnamelist[idx].lower() != "numberplate"
                ):  # all classe by default except numberplate
                    print("===executing elif")
                    cachedict["unique_id"].append(id_)
