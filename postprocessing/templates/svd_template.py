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
from src.number_plate_template import NumberPlateTemplate
from src.template_tracking import TemplateTracking
from PIL import ImageColor


class SVDTemplate(Template, Caching, IncidentExtract):
    def __init__(
        self, image, image_name, camera_id, image_time, steps, frame, incidents, usecase_id, boundary_config ,tracker=None, rcon=None
    ):
        """
        SVD Template Initilization
        Args:
            image (str): image in string
            image_name (str): name of image
            camera_id (str): camera id
            image_time (str): time of image captured
            steps (dict): all the steps of usecase
            frame (np.array): image as numpy array
            incidents (list): incidents list of usecase
            usecase_id (str or int): usecase id
            tracker (object): tracker object
            rcon (object): redis connection
            mask (np.array): mask image 1
            image_back (np.array): mask image2

        """
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
        cordkey=list(boundary_config.keys())
        image_height=int(boundary_config[cordkey[0]]["image_height"])
        image_width=int(boundary_config[cordkey[0]]["image_width"])
        self.color_l1=boundary_config[cordkey[0]]["color"]
        self.color_l2=boundary_config[cordkey[-1]]["color"]
        fr_h,fr_w,_c=frame.shape
        #self.y_l1, self.y_l2 = 360, 420  # 800 ,1000#800 ,1000#920 ,1200#412, 670
        print("=====keys====")
        self.y_l1, self.y_l2=int(boundary_config[cordkey[0]]["boundary_coordinates"]["y"][0]),int(boundary_config[cordkey[-1]]["boundary_coordinates"]["y"][-1])
        print("=======y1=====",self.y_l1)
        print("=======y2=====",self.y_l2)
        self.y_l1=int((self.y_l1/image_height)*fr_h)
        self.y_l2=int((self.y_l2/image_height)*fr_h)
        print("=======y1 after change=====",self.y_l1)
        print("=======y2 after change=====",self.y_l2)
        Template.__init__(self, image, image_name, camera_id, image_time, steps, frame)
        if self.rcon is not None:
            print("=======cahching initialization=====")
            Caching.__init__(self, self.rcon)
            print("====Caching INitilaize done")
            data = self.getbykey("svd", self.camera_id, self.usecase_id)

            if data is None:
                self.initialize_cache()

    def draw_line(self, frame, frame_width, line_list):
        for lin in line_list:
            cv2.line(frame, (lin[0], lin[1]), (frame_width, lin[-1]), color=(0, 255, 0), thickness=2)
        return frame

    def speed_cal(self, T1, T2, T3):
        print("======Calling Speed Calculation======")
        print(T1, T2, T3)
        print(type(T1), type(T2), type(T3))
        if T1 is not None:
            T1 = datetime.strptime(T1, "%Y-%m-%d %H:%M:%S.%f")
        if T2 is not None:
            T2 = datetime.strptime(T2, "%Y-%m-%d %H:%M:%S.%f")
        if T3 is not None:
            T3 = datetime.strptime(T3, "%Y-%m-%d %H:%M:%S.%f")
        # T1, T2, T3 = T1, T2, T3
        print("====Aftr float convrsion======")
        if T1 == T3:
            time_diff = (T2 - T1).total_seconds()
        elif T1 == T2:
            time_diff = (T3 - T2).total_seconds()
        elif T1 == T2 and T2 == T3:
            speed_res = 5
            print("going inside speed res ")
            return float(speed_res)
        else:
            time_diff_1 = (T2 - T1).total_seconds()
            time_diff_2 = (T3 - T2).total_seconds()
            time_diff = time_diff_1 + time_diff_2
            print("=======Time diff======", time_diff)
        if time_diff != 0:
            distance = 20  # meters
            speed_res = distance / time_diff
            speed_res = round(speed_res * 3.6, 2)
            print("speed :", speed_res)
        return float(speed_res)

    def line(self, frame, frame_width, frame_height):
        y_1 = max(0, min(frame_height - 1, self.y_l1))
        y_3 = max(0, min(frame_height - 1, self.y_l2))
        # line between line 1 and line 3
        y_2 = int((self.y_l1 + self.y_l2) // 2)
        y_2 = max(0, min(frame_height - 1, y_2))
        print("=========color l1=====",self.color_l1)
        print("=========color l1=====",self.color_l2)
        cv2.line(frame, (0, y_1), (frame_width, y_1), color=ImageColor.getcolor(self.color_l1,"RGB")[::-1], thickness=2)
        cv2.line(frame, (0, y_2), (frame_width, y_2), color=(0, 255, 0), thickness=2)
        cv2.line(frame, (0, y_3), (frame_width, y_3), color=ImageColor.getcolor(self.color_l2,"RGB")[::-1], thickness=2)
        line_one_ = [0, y_1, frame_width, y_1]
        line_two_ = [0, y_2, frame_width, y_2]
        line_three_ = [0, y_3, frame_width, y_3]
        list_lines = []
        list_lines.append(line_one_)
        list_lines.append(line_two_)
        list_lines.append(line_three_)
        frame = self.draw_line(frame, frame_width, list_lines)
        return frame, list_lines

    def check_up_down(self, line1_y1, line2_y1, y2):
        d1 = abs(line1_y1 - y2)
        d2 = abs(line2_y1 - y2)
        k = min(d1, d2)
        if k == d1:
            return "up"
        elif k == d2:
            return "down"

    def process_steps(self):
        '''
        Process the steps of usecase id
        returns :
            final_prediction (dict): filtered result based on preprocessing
            masked_image (dict): numpy array image
        '''
        print("=====template step proces=====")
        steps_keys = list(map(lambda x: int(x), list(self.steps.keys())))
        steps_keys.sort()
        print("========steps keys extracted=====")
        for ki in steps_keys:
            if ki == 1:
                step = self.steps[str(ki)]
                print("==========")
                #print(self.steps)
                #step["model_url"] = "http://172.16.0.204:6500/detect"
                print("model url:", step["model_url"])
                if step["step_type"] == "model":
                    # print('====list of exp classes :', list(step["classes"].values()))
                    self.expected_class.extend(list(step["classes"].values()))
                    print("=======inside model===")
                    self.model_call(step)
                    # print("====inside step model===")
                    print("=====detected class===")
                    print(self.detected_class)
                    # print('====len of detection :', len(self.detected_class))
                    if len(self.detected_class) > 0:
                        self.detection_init(self.detected_class, self.expected_class, self.image_time)
                        # DetectionProcess.__init__(self,self.detected_class,self.expected_class)
                        filtered_res = self.process_detection()
                        # print('====filter res :', filtered_res)
                        self.filtered_output.extend(filtered_res)
                        print("=====pred class==")
                        self.final_prediction["prediction_class"] = self.filtered_output
                        # print('==final pred :', self.final_prediction)
                else:
                    continue

            return self.final_prediction

    def np_plate_calc(self, vehicle_detection, numberplate_detection):
        print("====inside np plate calc=====")
        print("=========getting prediction========")
        vehicle_detection = vehicle_detection
        print("=====vehcile detection====")
        print(vehicle_detection)
        numberplate_detection = numberplate_detection
        print("=====np detection=======")
        print(numberplate_detection)
        print("=====filteration of np and vehicle done======")
        print("length of number plate===>", len(numberplate_detection))
        print("length of vehicle===>", len(vehicle_detection))
        if len(numberplate_detection) > 0:
            print("#" * 50)
            np_plate = NumberPlateTemplate(
                self.frame, self.usecase_id, self.camera_id, self.image_time, self.image_name
            )
            np_plate = np_plate.process_np(vehicle_detection, numberplate_detection, self.steps)
            print("predicted np plate=========")
            print(np_plate)
            print("%" * 50)
            return np_plate

    def process_data(self,logger):
        '''
        Process SVD Template
        Args:
            logger (object): Logger object
        returns:
            detection_data (list): list of detection data
            incident_dict (list): list of incident data
            self.expected_class (list): list of expected class
            masked_image (np.array): masked image as numpy array
        '''
        print("==============SVD==========")
        filtered_res_dict = []
        detection_incidentflag = {}
        detection_incidentflag["prediction_class"] = []
        self.process_steps()
        if "prediction_class" in self.final_prediction:
            filtered_res_dict = self.final_prediction["prediction_class"]
        # print('========tracker :', self.tracker)
        # print('========filter res :', filtered_res_dict)
        if self.tracker is not None:
            filtered_res_dict = self.tracker.track(self.image, filtered_res_dict)
        # =========check for up or down========
        print("=====tracking done=====")

        if len(filtered_res_dict) > 0:
            detection_dict = {}
            detection_dict["prediction_class"] = []
            print("=======going for svd======")
            np_image = "output/" + self.image_name
            frame, detection_dict["prediction_class"] = self.svd_calculation(filtered_res_dict)
            Computation.__init__(self, detection_dict, self.steps["2"], frame)
            print("=====computation started====")
            detection_dict = self.speed_computation()
            print("========speed comutation started=======")
            IncidentExtract.__init__(self, detection_dict, self.incidents, self.allsteps)
            print("======Incident detected=======")
            incident_dict, detection_incidentflag["prediction_class"] = self.vehicle_incident_svd()
            return detection_dict["prediction_class"], incident_dict, self.expected_class, frame

            # print("=======speed======")
            # print(detectlist)
        #     np_image = "output/"+self.image_name
        #     cv2.imwrite("output/"+self.image_name,frame)
        # cv2.imwrite("input/"+self.image_name,self.frame)
        else:
            return [], [], self.expected_class, None

        # TemplateTracking()
        # print("=========incident dict======")
        # print(incident_dict)
        # return filtered_res_dict, incident_dict

    def initialize_cache(self):
        print("=====start caching initialization=====")
        cachedict = {}
        cachedict["unique_id"] = []
        cachedict["unique_id_direction"] = []
        cachedict["object_dict"] = {}
        cachedict["time_dict"] = {}
        cachedict["detections"] = []
        print("======caching initialization done====")
        self.setbykey("svd", self.camera_id, self.usecase_id, cachedict)
        print("=====cache dict saved to cache")
        # return cachedict

    def speedbypixel(self, idx, time, x, y, x_change, y_change):
        speedpixel = []
        cf = []
        speedms = []
        averagecf = 0
        speedms2 = []
        for i in range(1, len(x)):
            start = (x[i - 1], y[i - 1])
            end = (x[i], y[i])
            startx = x_change[i - 1]
            endx = x_change[i]
            cf.append(2 / x_change[i])
            cf.append(2 / x_change[i - 1])

            start_time = datetime.strptime(time[i - 1], "%Y-%m-%d %H:%M:%S.%f")
            end_time = datetime.strptime(time[i], "%Y-%m-%d %H:%M:%S.%f")
            distance = round(np.sqrt(((start[0] - end[0]) ** 2) + ((start[1] - end[1]) ** 2)), 2)
            timespent = np.abs((end_time - start_time).total_seconds())

            speedpixel.append(round(distance / timespent, 2))
            averagecf = np.mean(cf)
            speedms.append((distance / averagecf) / timespent)
            speedms2.append((distance * averagecf) / timespent)

        print("speed===>", speedpixel)
        print("speed in m/s===>", speedms)
        print("speed of vehicle in pixel==>", round(np.mean(speedpixel), 2))
        print("speed in m/s===>", round(np.mean(speedms), 2))
        print("speed ms2===>", speedms2)
        return round(np.mean(speedms), 2)

    def pixel_displacement(self, detectionlist, idx):
        required_dict_det = list(filter(lambda x: int(x["id"]) == int(idx), detectionlist))
        total_time = list([x["image_time"] for x in required_dict_det])
        xmin = list([x["xmin"] for x in required_dict_det])
        ymin = list([x["ymin"] for x in required_dict_det])
        xmax = list([x["xmax"] for x in required_dict_det])
        ymax = list([x["ymax"] for x in required_dict_det])
        x = list([(x["xmin"] + x["xmax"]) for x in required_dict_det])
        y = list([(x["ymin"] + x["ymax"]) for x in required_dict_det])
        x_change = list([(x["xmax"] - x["xmin"]) for x in required_dict_det])
        y_change = list([(x["ymax"] - x["ymin"]) for x in required_dict_det])
        return self.speedbypixel(idx, total_time, x, y, x_change, y_change)

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
        trackids = [i["id"] for i in filtered_res_dict if i["class_name"] == "car"]
        classidlist = [i["class_id"] for i in filtered_res_dict if i["class_name"] == "car"]
        classnamelist = [i["class_id"] for i in filtered_res_dict if i["class_name"] == "car"]
        detectlist = [i for i in filtered_res_dict]  # if i["class_name"]== "car"]
        nplist = [i for i in filtered_res_dict if i["class_name"] == "numberplate"]
        print("======detections======")
        # print(self.image_time)
        print(detectlist)
        detection_speed_list = None
        vehicle_speed = 0
        h, w, c = self.frame.shape
        frame, line_list = self.line(self.frame, w, h)
        id_list = []
        cachedict = self.getbykey(
            "svd",
            self.camera_id,
            self.usecase_id,
        )
        if cachedict is None:
            self.initialize_cache()
        else:
            cachedict = self.getbykey("svd", self.camera_id, self.usecase_id)
            cachedict["detections"].extend(filtered_res_dict)
            print("=====cachedict====")
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
                    # speed=self.pixel_displacement(cachedict["detections"],id_)
                    # print("======updatig speed list====")
                    # if detection_speed_list is None:
                    #     detection_speed_list=self.update_speed(detectlist,id_,speed)
                    # else:
                    #     detection_speed_list=self.update_speed(detection_speed_list,id_,speed)
                    # print("======speed list updated====")

                elif (
                    classnamelist[idx].lower() != "np" or classnamelist[idx].lower() != "numberplate"
                ):  # all classe by default except numberplate
                    print("===executing elif")
                    cachedict["unique_id"].append(id_)
                    print("=====checking firction====")
                    detectlist[idx]["direction"] = self.check_up_down(
                        line_list[0][1], line_list[2][1], detectlist[idx]["ymax"]
                    )
                    print("===updating state===")
                    detectlist[idx]["state"] = False
                    print("====updating unique direction===")
                    # print('detection list:', detectlist[idx])
                    cachedict["unique_id_direction"].append([id_, detectlist[idx]])
                    print("======checking time dict====")
                    if id_ not in cachedict["time_dict"]:
                        cachedict["time_dict"][str(id_)] = {
                            "t1": None,
                            "t2": None,
                            "t3": None,
                            "class": None,
                            "x1": None,
                            "y1": None,
                            "x2": None,
                            "y2": None,
                            "speed": None,
                            "dir": None,
                            "numberplate_dict": {},
                        }
                    # print('chache_dict========')
                    # print(cachedict["time_dict"])
                # print("======fetchig det===",idx)
                # det = detectlist[idx]
                print("====Got Det====")
                if len(cachedict["unique_id_direction"]) > 0:
                    for j in range(0, len(cachedict["unique_id_direction"])):
                        if (
                            cachedict["unique_id_direction"][j][0] in trackids
                            and cachedict["unique_id_direction"][j][1]["direction"] == "down"
                            and cachedict["unique_id_direction"][j][1]["class_name"] == "car"
                        ):
                            # print("====checking for down====",j)
                            # print(cachedict["unique_id_direction"][j][1])
                            # print("=====condition check===")
                            obj_id = cachedict["unique_id_direction"][j][0]
                            class_name = cachedict["unique_id_direction"][j][1]["class_name"]
                            dir_down = cachedict["unique_id_direction"][j][1]["direction"]
                            # print("===geting object id====")
                            for id_, box_ in id_list:
                                if id_ == obj_id:
                                    print("====Box checking====")
                                    (
                                        cachedict["time_dict"][str(obj_id)]["x1"],
                                        cachedict["time_dict"][str(obj_id)]["y1"],
                                        cachedict["time_dict"][str(obj_id)]["x2"],
                                        cachedict["time_dict"][str(obj_id)]["y2"],
                                    ) = box_
                            # print("=====Box checking done=====")
                            if (
                                cachedict["time_dict"][str(obj_id)]["y2"] is not None
                                and cachedict["time_dict"][str(obj_id)]["y2"] <= line_list[2][1]
                            ):
                                if cachedict["time_dict"][str(obj_id)]["t1"] is None:
                                    print("t1 :", str(self.image_time), "========", self.image_time)
                                    cachedict["time_dict"][str(obj_id)]["t1"] = str(self.image_time)
                                    vehicle_detectdown = [i for i in filtered_res_dict if i["class_name"] == "car"]
                                    nplist = [i for i in filtered_res_dict if i["class_name"] == "numberplate"]
                                if cachedict["time_dict"][str(obj_id)]["class"] is None:
                                    cachedict["time_dict"][str(obj_id)]["class"] = class_name
                                if cachedict["time_dict"][str(obj_id)]["dir"] is None:
                                    cachedict["time_dict"][str(obj_id)]["dir"] = dir_down
                                if cachedict["time_dict"][str(obj_id)]["y2"] > line_list[1][1]:
                                    if cachedict["time_dict"][str(obj_id)]["t2"] is None:
                                        cachedict["time_dict"][str(obj_id)]["t2"] = str(self.image_time)
                                if cachedict["time_dict"][str(obj_id)]["y2"] > line_list[0][1]:
                                    if cachedict["time_dict"][str(obj_id)]["t3"] is None:
                                        cachedict["time_dict"][str(obj_id)]["t3"] = str(self.image_time)
                                print("time dict down :", cachedict["time_dict"])
                            if (
                                cachedict["time_dict"][str(obj_id)]["t1"] is not None
                                and cachedict["time_dict"][str(obj_id)]["t2"] is not None
                                and cachedict["time_dict"][str(obj_id)]["t3"] is not None
                                and cachedict["time_dict"][str(obj_id)]["class"] == "car"
                            ):
                                try:
                                    print("::::::processing for down ids:::::")
                                    vehicle_speed = self.speed_cal(
                                        cachedict["time_dict"][str(obj_id)]["t1"],
                                        cachedict["time_dict"][str(obj_id)]["t2"],
                                        cachedict["time_dict"][str(obj_id)]["t3"],
                                    )
                                    print("speed ::", vehicle_speed)
                                    cachedict["time_dict"][str(obj_id)]["speed"] = vehicle_speed
                                    if float(cachedict["time_dict"][str(obj_id)]["speed"]) > 0:
                                        print("=====calling np func======")
                                        vehicle_detection = [i for i in filtered_res_dict if i["id"] == obj_id]
                                        # self.np_plate_calc(vehicle_detectdown,nplist)
                                        npdet = self.np_plate_calc(vehicle_detection, nplist)
                                        cachedict["time_dict"]["numberplate_dict"] = npdet
                                        print("=======npdet========")
                                        print(npdet)
                                    print("Object ID:", obj_id, "Speed:", vehicle_speed, "kmph")
                                    print("time dict down :", cachedict["time_dict"])
                                    for j in range(len(npdet)):
                                        npdet[j]["speed"] = vehicle_speed
                                    print("==after update====")
                                    print(npdet)
                                    detectlist = npdet
                                    # detectlist[idx]["np_plate"] = npdet
                                    print("========detection list=====")
                                    print(detectlist)
                                except:
                                    pass

                        if (
                            cachedict["unique_id_direction"][j][0] in trackids
                            and cachedict["unique_id_direction"][j][1]["direction"] == "up"
                            and cachedict["unique_id_direction"][j][1]["class_name"] == "car"
                        ):
                            # print("=======checking for up====",j)
                            # print(cachedict["unique_id_direction"][j][1])
                            obj_id = cachedict["unique_id_direction"][j][0]
                            class_name = cachedict["unique_id_direction"][j][1]["class_name"]
                            dir_up = cachedict["unique_id_direction"][j][1]["direction"]
                            # nplist = [i for i in filtered_res_dict if i["class_name"]== "numberplate"]
                            print("======obj id got=====")
                            for id_, box_ in id_list:
                                if id_ == obj_id:
                                    print("===checking time dict====")
                                    (
                                        cachedict["time_dict"][str(obj_id)]["x1"],
                                        cachedict["time_dict"][str(obj_id)]["y1"],
                                        cachedict["time_dict"][str(obj_id)]["x2"],
                                        cachedict["time_dict"][str(obj_id)]["y2"],
                                    ) = box_
                            # print('id:',obj_id, 'y2 :', cachedict["time_dict"][str(obj_id)]['y2'], 'line1:', line_list[0][1], 'line2:', line_list[1][1], 'line3:', line_list[2][1])

                            if (
                                cachedict["time_dict"][str(obj_id)]["y2"] is not None
                                and cachedict["time_dict"][str(obj_id)]["y2"] >= line_list[0][1]
                            ):
                                print("====time checking")
                                if cachedict["time_dict"][str(obj_id)]["t1"] is None:
                                    cachedict["time_dict"][str(obj_id)]["t1"] = str(self.image_time)
                                    if cachedict["time_dict"][str(obj_id)]["class"] is None:
                                        cachedict["time_dict"][str(obj_id)]["class"] = class_name
                                    if cachedict["time_dict"][str(obj_id)]["dir"] is None:
                                        cachedict["time_dict"][str(obj_id)]["dir"] = dir_up
                                if cachedict["time_dict"][str(obj_id)]["y2"] > line_list[1][1]:
                                    if cachedict["time_dict"][str(obj_id)]["t2"] is None:
                                        cachedict["time_dict"][str(obj_id)]["t2"] = str(self.image_time)
                                # print('y2 :', cachedict["time_dict"][str(obj_id)]['y2'], 'line2:{}, line3:{}'.format(line_list[1][1], line_list[2][1]))
                                if cachedict["time_dict"][str(obj_id)]["y2"] > line_list[2][1]:
                                    if cachedict["time_dict"][str(obj_id)]["t3"] is None:
                                        # print('y2 :', cachedict["time_dict"][str(obj_id)]['y2'], 'line3:{}'.format(line_list[2][1]))
                                        cachedict["time_dict"][str(obj_id)]["t3"] = str(self.image_time)
                                print("====time dict up=======")
                                print(cachedict["time_dict"])
                            if (
                                cachedict["time_dict"][str(obj_id)]["t1"] is not None
                                and cachedict["time_dict"][str(obj_id)]["t2"] is not None
                                and cachedict["time_dict"][str(obj_id)]["t3"] is not None
                                and cachedict["time_dict"][str(obj_id)]["class"] == "car"
                            ):
                                try:
                                    print("::::::processing for up ids:::::")
                                    vehicle_speed = self.speed_cal(
                                        cachedict["time_dict"][str(obj_id)]["t1"],
                                        cachedict["time_dict"][str(obj_id)]["t2"],
                                        cachedict["time_dict"][str(obj_id)]["t3"],
                                    )
                                    print("speed ::", vehicle_speed)
                                    cachedict["time_dict"][str(obj_id)]["speed"] = vehicle_speed
                                    if cachedict["time_dict"][str(obj_id)]["speed"] > 0:
                                        print("=====calling np func======")
                                        vehicle_detection = [i for i in filtered_res_dict if i["id"] == obj_id]
                                        npdet = self.np_plate_calc(vehicle_detection, nplist)
                                        cachedict["time_dict"]["numberplate_dict"] = npdet
                                        print("=======npdet========")
                                        print(npdet)
                                    print("Object ID:", obj_id, "Speed:", vehicle_speed, "kmph")
                                    print("time dict up :", cachedict["time_dict"])
                                    for j in range(len(npdet)):
                                        npdet[j]["speed"] = float(vehicle_speed)
                                    print("==after update====")
                                    print(npdet)
                                    detectlist = npdet
                                    # detectlist[idx]["np_plate"] = npdet
                                    print("=====np plate in detectlist========")
                                    print(detectlist)
                                    # print('=============')
                                    # print(detectlist)
                                except:
                                    pass
        print("#########################")
        print("=====saving cache====")
        if len(detectlist) > 0:
            self.setbykey("svd", self.camera_id, self.usecase_id, cachedict)
        print("======saving done===")
        print("#########################")

        # if detection_speed_list is None:
        print("&" * 30)
        print(detectlist)

        print("^" * 30)
        return frame, detectlist
