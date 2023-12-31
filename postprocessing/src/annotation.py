'''
Frame Annotation
'''
from datetime import datetime

import cv2
import numpy as np
from PIL import ImageColor
import copy

class AnnotateImage:
    def __init__(self, expected_class, detected_class, frame, misc_data=None):
        """
        Frame Annotation
        Args:
            expected_class (list): list of class to annotate
            detected_class (list): result of model detection
            frame (np.array): numpy array
            misc_data (list): result of model computation
        """
        self.expected_class = expected_class
        self.detected_class = detected_class
        self.frame = frame
        self.misc_data = misc_data

    def create_legend(self):
        '''
        In case of ecternal legend, this will create legend after taking 20% of the image
        returns:
            legend (np.array): area to put legends
        '''
        h, w, c = self.frame.shape
        legend = np.full(shape=(h, int(0.2 * w), c), fill_value=255, dtype=self.frame.dtype)
        return legend

    def external_legend(self, frame,expected_classes,detected_class):
        '''
        Mark external legend on image
        Args:
            frame (np.array):  numpy array
        returns:
            frame (np.array):  numpy array
        '''
        h, w, c = frame.shape
        FONT_SCALE = 0.5
        legend = self.create_legend()
        frame = cv2.hconcat([frame, legend])
        totaldetected_class = len(detected_class)
        pixeldiff_h, pixeldiff_w, pixeldiff_c = frame.shape
        start_pixel_h = 30
        class_ids = [i["class_id"] for i in expected_classes]
        # start_pixel_w=pixeldiff_w-int(0.2*w)+10
        track_name_list = []
        np_list = []
        present_class_id = []
        present_class_name = []
        for det in detected_class:
            # print("===annot detect===")
            try:
                class_id = det["class_id"]
            except:
                return frame
            # print(self.expected_class)
            # print(class_ids)
            # print(class_id)
            # print("======")
            # print(class_ids.index(int(class_id)))
            # print("+++++")
            expected_class = expected_classes[class_ids.index(int(class_id))]
            # print("===got exected class====")
            # frame=cv2.putText(frame,det["class_name"],org=(start_pixel_w,start_pixel_h),
            # fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5,color=ImageColor.getcolor(expected_class["text_color"], "RGB"),
            # thickness=3)
            # cv2.imwrite("font.jpg",frame)
            width = int(det["xmax"]) - int(det["xmin"])
            height = int(det["ymax"]) - int(det["ymin"])
            # frame=cv2.circle(frame,( start_pixel_w+70, start_pixel_h-3),5, ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1], cv2.FILLED)
            frame = cv2.rectangle(
                frame,
                (det["xmin"], det["ymin"]),
                (det["xmax"], det["ymax"]),
                color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                thickness=expected_class["bound_thickness"],
            )
            if det["class_name"] in det and type(det[det["class_name"]])== type('abc'):
                cv2.rectangle(
                    frame,
                    (det["xmin"], det["ymin"]),
                    (det["xmin"] + (det["xmax"] - det["xmin"]), det["ymin"] - 30),
                    color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                    thickness=1,
                )
                cv2.putText(
                    frame,
                    str(det[det["class_name"]]),
                    (int(det["xmin"]), int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    (0, 0, 0),
                    thickness=expected_class["text_thickness"]
                )
            if "speed" in det:
                cv2.rectangle(
                    frame,
                    (det["xmin"], det["ymin"]),
                    (det["xmin"] + (det["xmax"] - det["xmin"]), det["ymin"] - 30),
                    color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                    thickness=-1,
                )
                cv2.putText(
                    frame,
                    str(det["speed"]),
                    (int(det["xmin"]), int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    (0, 0, 0),
                    thickness=expected_class["text_thickness"]
                )

            present_class_id.append(class_id)
            present_class_name.append(det["class_name"])
        present_class_id = list(set(present_class_id))
        present_class_name = list(set(present_class_name))
        # print("=====external annotation======")
        for clas, idcls in zip(present_class_name, present_class_id):
            # print("======annot=====",idcls,clas)
            expected_class = self.expected_class[class_ids.index(int(idcls))]
            # print("======annot2=====",w,h)
            # print(frame.shape)
            start_pixel_w = int(w + 0.01 * w)
            start_pixel_h = start_pixel_h + 10
            # print(start_pixel_h,start_pixel_w)
            frame = cv2.circle(
                frame,
                (start_pixel_w, start_pixel_h),
                5,
                ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                cv2.FILLED,
            )
            frame = cv2.putText(
                frame,
                clas,
                org=(start_pixel_w + 10, start_pixel_h),
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.5,
                color=(0,0,0),
                thickness=2,
            )
            # print("======annot3=====")
            start_pixel_h = start_pixel_h + 40
        return frame

    def internal_legend(self, frame,expected_classes,detected_class):
        '''
        Annotate internally on image
        Args:
            frame (np.array):  numpy array
        returns:
            frame (np.array):  numpy array
        '''
        # print("====internal legend=======")
        FONT_SCALE = 0.5
        try:
            # print("====class id====")
            class_ids = [i["class_id"] for i in expected_classes]
            # ids=[i["id"] for i in self.expected_class ]
            # print("=======det====")
            # print(self.detected_class)
            for det in detected_class:
                # print(det)
                x1 = det["xmin"]
                y1 = det["ymin"]
                x2 = det["xmax"]
                y2 = det["ymax"]
                class_name = det["class_name"]
                # print("=*********")
                width = int(x2) - int(x1)
                height = int(y2) - int(y1)
                class_id = det["class_id"]
                # print("=======expected====")
                expected_class = expected_classes[class_id.index(str(class_id))]

                # overlap = output[i]["overlap"]
                # print("=======annotation====")
                print("====Image color====")
                print(class_name, det["id"])
                print(ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1])

                frame = cv2.rectangle(
                    frame,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                    thickness=expected_class["text_thickness"],
                )
                # cv2.rectangle(image, (int(x1), int(y1)), (int(x1)+(int(x2) - int(x1)), int(y1) - 10), color=color_code[class_name],
                #             thickness=-1)
                # print("=====text========")
                if det["id"] is  None:
                    
                    cv2.rectangle(
                        frame,
                        (int(x1), int(y1)),
                        (int(x1) + (int(x2) - int(x1)), int(y1) - 30),
                        color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                        thickness=-1,
                    )
                    frame = cv2.putText(
                        frame,
                        class_name,
                        (int(x1), int(y1)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color=ImageColor.getcolor(expected_class["text_color"], "RGB")[::-1],
                        thickness=1
                    )
                else:
                    cv2.rectangle(
                        frame,
                        (int(x1), int(y1)),
                        (int(x1) + (int(x2) - int(x1)), int(y1) - 30),
                        color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                        thickness=-1,
                    )
                    frame = cv2.putText(
                        frame,
                        class_name ,
                        (int(x1), int(y1)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color=ImageColor.getcolor(expected_class["text_color"], "RGB")[::-1],
                        thickness=1
                    )
                if det["class_name"] in det and  type(det[det["class_name"]])== type('abc') and len(det[det["class_name"]]) > 0:
                    # cv2.rectangle(
                    #     frame,
                    #     (det["xmin"], det["ymin"]),
                    #     (det["xmin"] + (det["xmax"] - det["xmin"]), det["ymin"] - 30),
                    #     color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                    #     thickness=-1,
                    # )
                    cv2.putText(
                        frame,
                        str(det[det["class_name"]]),
                        (int(x1)+20, int(y1)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5,
                color=ImageColor.getcolor(expected_class["text_color"], "RGB")[::-1],
                thickness=2
                    )
                if "speed" in det:
                    # cv2.rectangle(
                    #     frame,
                    #     (det["xmin"], det["ymin"]),
                    #     (det["xmin"] + (det["xmax"] - det["xmin"]), det["ymin"] - 30),
                    #     color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                    #     thickness=-1,
                    # )
                    cv2.putText(
                        frame,
                        str(det["speed"]),
                        (int(x1)+40, int(y1)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5,
                color=(0,0,0),
                thickness=2,
                    )

                # cv2.imwrite("annot_frame/"+str(datetime.utcnow())+".jpg",frame)
        except Exception as ex:
            print("Exception while annotation===>", ex)
        return frame

    def annotate_computation(self, frame,misc_data):
        '''
        Anntate computation image
        Args:
            frame (np.array):  numpy array
        returns:
            frame (np.array):  numpy array
        '''
        
        x1 = 10
        width, height, _ = frame.shape
        y1 = 30
        fontScale = 0.005
        print("======+++++misc___annotate",misc_data)
        if misc_data is not None:
            for i in misc_data:
                y1 = y1 + int(0.05 * width)

                frame = cv2.putText(
                    frame,
                    i["text"] + ": " + str(i["data"]),
                    (x1, y1),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    int(min(width, height) * fontScale) + 1,
                    color=(255, 0, 0),
                    thickness=2,
                )
                # cv2.imwrite("abc.jpg",frame)
        return frame

    def annotate(self, legend_state=0):
        '''
        Annotate externally or internaly on frame
        Args:
            legend_state (int): 0 for internal_legend, 1 for external_legend
        returns:
            frame (np.array): numpy array
        '''
        # print("====annotation called===")
        frame = np.copy(self.frame)
        misc_data=copy.deepcopy(self.misc_data)
        expected_classes=copy.deepcopy(self.expected_class)
        detected_class=copy.deepcopy(self.detected_class)
        frame = self.annotate_computation(frame,misc_data)

        # h,w,c=frame.shape
        if len(self.detected_class) > 0:
            # frame=self.external_legend(frame)
            try:
                if int(legend_state) == 1:
                    # print("====exter legend====")
                    frame = self.external_legend(frame,expected_classes,detected_class)
                else:
                    # print("====internal legend====")
                    frame = self.internal_legend(frame,expected_classes,detected_class)
            except:
                # print("====internal legend exceptions====")
                frame = self.internal_legend(frame,expected_classes,detected_class)
        del self.expected_class, self.detected_class,self.misc_data, misc_data,expected_classes,detected_class
        return frame
