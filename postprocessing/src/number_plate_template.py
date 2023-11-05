import cv2
import numpy as np
import requests


class NumberPlateTemplate:
    def __init__(self, frame, usecase_id, camera_id, image_time, image_name):
        print("========Number Plate Initialization====")
        self.frame = frame
        self.usecase_id = usecase_id
        self.camera_id = camera_id
        self.image_time = image_time
        self.image_name = image_name
        print("=====number plate initialization done=====")

    def create_request_np(self, imagelist, npcords, model_type, model_framework):
        requestparams = {}
        requestparams["image"] = imagelist
        requestparams["image_name"] = self.image_name
        requestparams["np_coord"] = npcords

        requestparams["model_config"] = {}
        return requestparams

    def api_call_np(self, url, requestparams):
        # self.model_urls.append(url)
        print("=======Api Calling=====", url)
        try:
            # print(requestparams)
            response = requests.post(url, json=requestparams)
            # current_time=datetime.utcnow()

            # time_diff=(current_time-self.image_time).total_seconds()
            # self.logger.info(f"{self.usecase_id}, {self.camera_id}, model response time, {time_diff}")
            print("=====model result NP=====")
            #print(response.json())
            return response
        except Exception as ex:
            print("=====url======")
            print("====model call exception====", ex)
            # print(self.requestparams)
            return None

    def np_model_call(self, npcords, step):
        print("========Number Plate model call====")
        url = step["model_url"]
        image_str = cv2.imencode(".jpg", self.frame)[1].tobytes().decode("ISO-8859-1")
        requestparams = self.create_request_np(image_str, npcords, step["model_type"], step["model_framework"])
        print("====calling api=====")
        response = self.api_call_np(url, requestparams)
        if response is not None:
            data = response.json()["data"]
            print("=====number plate response====")
            #print(data)
            return data
        else:
            return []

    def overlap(self, Xmin, Ymin, Xmax, Ymax, Xmin1, Ymin1, Xmax1, Ymax1):
        if Xmin > Xmax1 or Xmin1 > Xmax or Ymin > Ymax1 or Ymin1 > Ymax:
            ov = 0
        else:
            ov = (max(Xmin, Xmin1) - min(Xmax, Xmax1)) * (max(Ymin, Ymin1) - min(Ymax, Ymax1))
        return round(100 * ov / ((Xmax1 - Xmin1) * (Ymax1 - Ymin1)), 1)

    def find_vehicle(self, vehicle_detction, np_detection):
        listres = []
        print("========Number Plate Vehicle Call====")
        allindex=[]
        commonindex=[]
        for idx,vech in enumerate(vehicle_detction):
            allindex.append(idx)
            for np in np_detection:
                if "text" in np:
                    
                    ovlp = self.overlap(
                        vech["xmin"],
                        vech["ymin"],
                        vech["xmax"],
                        vech["ymax"],
                        np["xmin"],
                        np["ymin"],
                        np["xmax"],
                        np["ymax"],
                    )
                    print(ovlp)
                    if ovlp >= 90:
                        commonindex.append(idx)
                        vech[vech["class_name"]] = np["text"]
                        listres.append(vech)
                        break
                    else:
                        pass
            
            #listres.append(vech)
        
        commonindex=list(set(commonindex))
        listres=[vehicle_detction[i] for i in commonindex]
        return listres

    def process_np(self, vehicle_detction, np_detection, step):
        #imagelist = []
        listresult = []
        np_output = []
        carwithNp = []
        npcords = {}
        print("Number plate Process")

        for  stp in step:
            step_process = step[stp]
            print(stp)
            print("==step processs============")
            print(step_process)
            if "model_type" not in step_process:
                continue

            if step_process["model_type"].lower() == "ocr":
                print("====going for np detectction====", len(np_detection))
                print(np_detection)
                for ix, det in enumerate(np_detection):
                    xmin = det["xmin"]
                    ymin = det["ymin"]
                    xmax = det["xmax"]
                    ymax = det["ymax"]
                    np_image = self.frame[ymin:ymax, xmin:xmax]
                    #cv2.imwrite("np/" + self.image_name, np_image)
                    # np_image_str=cv2.imencode(".jpg", np_image)[1].tobytes().decode("ISO-8859-1")
                    npcords[ix + 1] = [xmin, ymin, xmax, ymax]
                print("====npcords===>", npcords)

                np_output = self.np_model_call(npcords, step_process)
                # print(np_output)
        for det, np in zip(np_detection, np_output):
            if "np" in np:
                det["text"] = np["np"]
            listresult.append(det)
        carwithNp = self.find_vehicle(vehicle_detction, listresult)
        return carwithNp
