import json


class VerifyCache:
    def __init__(self, rcon):
        self.rcon = rcon

    def overlap(self, Xmin, Ymin, Xmax, Ymax, Xmin1, Ymin1, Xmax1, Ymax1):
        if Xmin > Xmax1 or Xmin1 > Xmax or Ymin > Ymax1 or Ymin1 > Ymax:
            ov = 0
        else:
            ov = (max(Xmin, Xmin1) - min(Xmax, Xmax1)) * (max(Ymin, Ymin1) - min(Ymax, Ymax1))
        return round(100 * ov / ((Xmax1 - Xmin1) * (Ymax1 - Ymin1)), 1)

    def get_track_data(self, usecase_id, cam_id):
        usecase_track_data = self.rcon.get(str(usecase_id) + "_" + str(cam_id))
        print("====cache===", usecase_track_data)
        if usecase_track_data is None:
            print("===if executed===")
            return {}
        usecase_track_data_json = json.loads(usecase_track_data)
        cam_track_data = usecase_track_data_json[str(cam_id)]
        return cam_track_data

    def filter_track_data_byid(self, detection, usecase_id, cam_id):
        usecase_track_data = self.get_track_data(usecase_id, cam_id)
        track_data_image = []

        track_cam_data = list(usecase_track_data.values())

        track_data_image = sum(track_cam_data, [])
        common_data = []
        diff_data = []
        for trk in track_data_image:
            for det in detection:
                if trk["id"] == det["id"] and trk["class_name"] == det["class_name"]:
                    common_data.append(det)
                else:
                    diff_data.append(det)
        return common_data, diff_data

    def divide_data_by_class(self, track_cam_data):
        """
        This method will take the previous tracking data of camera{"img_name_1":[det1,det2],"image_name_2",["det1","det2]}
        and then convert them in format of class {det["class_name"]:[image_name_1_det1_cord,image_name_2_det2_cord]}
        """
        class_dict_track_data = {}
        for track_img_data in track_cam_data:
            track_img_det_data = track_cam_data[track_img_data]
            for det in track_img_det_data:
                if det["class_name"] not in class_dict_track_data.keys():
                    class_dict_track_data[det["class_name"]] = [
                        {"xmin": det["xmin"], "ymin": det["ymin"], "xmax": det["xmax"], "ymax": det["ymax"]}
                    ]
                else:
                    class_dict_track_data[det["class_name"]].append(
                        {"xmin": det["xmin"], "ymin": det["ymin"], "xmax": det["xmax"], "ymax": det["ymax"]}
                    )
        return class_dict_track_data

    def filter_track_data_byoverlap(self, detection, usecase_id, cam_id):
        """"""
        cam_track_data = self.get_track_data(usecase_id, cam_id)
        print("====usecase_track==", cam_track_data)
        print("overlap_cam_track_data===>", cam_track_data)
        print("detection_data===>", detection)
        if len(cam_track_data) == 0:
            return detection, detection
        track_cam_data = cam_track_data
        track_data_image = list(track_cam_data.values())
        class_track_data = self.divide_data_by_class(track_cam_data)
        print("=====class_track_data==", class_track_data)
        common_data = []
        diff_data = []

        for det in detection:
            if det["class_name"] in list(class_track_data.keys()):
                for trk in class_track_data[det["class_name"]]:
                    trk_cord = trk
                    overlap = self.overlap(
                        trk["xmin"],
                        trk["ymin"],
                        trk["xmax"],
                        trk["ymax"],
                        det["xmin"],
                        det["ymin"],
                        det["xmax"],
                        det["ymax"],
                    )
                    print("======overlap====", overlap)
                    if overlap >= 80:
                        common_data.append(det)
                    else:
                        diff_data.append(det)

            else:
                diff_data.append(det)
        return common_data, diff_data

    def filter_track_data(self, usecase_id, cam_id, detection_data, image_name, byid=True, byoverlap=False):
        usecase_track_data = {}
        track_data = self.get_track_data(usecase_id, cam_id)
        common_data = {}
        diff_data = {}

        if len(track_data) > 0:
            if byid:
                # filter data by tracking id given by model after comparing if conseutive
                # frames have been assigned with same id for same class
                common_data, diff_data = self.filter_track_data_byid(detection_data, usecase_id, cam_id)
                # return common_data, diff_data
            if byoverlap:
                # filter data by tracking overlap, will compare the data from previous frames for detection in
                # similar region
                common_data, diff_data = self.filter_track_data_byoverlap(detection_data, usecase_id, cam_id)
                # return common_data, diff_data

        if len(track_data) > 9:
            track_data_keys = list(track_data[cam_id].keys()).sort()
            for i in range(9, len(track_data_keys)):
                del track_data[cam_id][i]

        elif len(track_data) == 0:
            # usecase_track_data={}
            # track_data=json.dupms(self.rcon.get(usecase_id))
            track_data = {}
            print("camera_track_data cache====>", track_data)
            track_data[image_name] = detection_data
            common_data = detection_data
            diff_data = detection_data

        else:
            track_data[image_name] = detection_data

        usecase_track_data[cam_id] = track_data
        print("usecase_track_data cache====>", usecase_track_data)
        self.rcon.set(str(usecase_id) + "_" + str(cam_id), json.dumps(usecase_track_data))
        return common_data, diff_data
