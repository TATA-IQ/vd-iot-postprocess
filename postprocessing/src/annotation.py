'''
Frame Annotation
'''
from datetime import datetime

import cv2
import numpy as np
from PIL import ImageColor
import copy
import math
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
    def bottom_legend(self,frame,expected_classes, detected_class):
        h, w, c = frame.shape
        label_height=30
        box_width=20
        box_height=20
        label_per_row=4
        label_height=30
        class_ids = [i["class_id"] for i in expected_classes]
        detcetd_class_ids=[ i["class_id"] for i in detected_class]

        label_row = math.ceil(len(list(set(detcetd_class_ids)))/label_per_row)
        label_width = int(frame.shape[1]/label_per_row)
        img_label = np.zeros([label_row*label_height, frame.shape[1],3],dtype=np.uint8)
        img_label.fill(255)
        i = 0
        j = 0
        xgap = 5
        ygap = 5
        unique_class=list(set([i["class_name"] for i in detected_class]))
        unique_class_id=list(set([i["class_id"] for i in detected_class]))
        for cls,idx in zip(unique_class,unique_class_id):
            expected_class = expected_classes[class_ids.index(int(idx))]
            xo,  yo = i*label_width, j*label_height
            bound_color=ImageColor.getcolor(expected_class["bound_color"],"RGB")[::-1]
            text_color=ImageColor.getcolor(expected_class["text_color"],"RGB")[::-1]
            bound_thickness=expected_class["bound_thickness"]
            text_thickness=expected_class["text_thickness"]
            img_label = cv2.rectangle(img_label, (int(xo+xgap), int(yo+ygap)), (int(xo+xgap+box_width), int(yo+ygap+box_height)), bound_color, bound_thickness)
            img_label = cv2.putText(img_label, expected_class["class_name"], (int(xo+box_width+2*xgap), int(yo+ygap+box_height)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color,text_thickness)
            i+=1
            if(i>=label_per_row):
                i=0
                j+=1
        for det in detected_class:
            class_id=det["class_id"]
            expected_class = expected_classes[class_ids.index(int(class_id))]
            bound_color=ImageColor.getcolor(expected_class["bound_color"],"RGB")[::-1]
            text_color=ImageColor.getcolor(expected_class["text_color"],"RGB")[::-1]
            bound_thickness=expected_class["bound_thickness"]
            text_thickness=expected_class["text_thickness"]
            xmin,ymin,xmax,ymax=det["xmin"],det["ymin"],det["xmax"],det["ymax"]
            class_id=det["class_id"]
            
            cv2.rectangle(frame,(xmin, ymin),(xmax,ymax),bound_color,bound_thickness)
            cv2.rectangle(
                    frame,
                    (det["xmin"], det["ymin"]),
                    (det["xmin"] + (det["xmax"] - det["xmin"]), det["ymin"] - 30),
                    bound_color,
                    -1
                )
            if det["class_name"] in det and type(det[det["class_name"]])== type('abc'):
               
                cv2.putText(
                    frame,
                    str(det[det["class_name"]]),
                    (int(det["xmin"]), int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    text_color,
                    thickness=text_thickness
                )
            if "speed" in det:
                cv2.putText(
                    frame,
                    str(det["speed"])+" kmph",
                    (int(det["xmax"])-30, int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    text_color,
                    thickness=text_thickness
                )



            
        image_final = cv2.vconcat([frame, img_label])

        return image_final



    def top_legend(self,frame,expected_classes, detected_class):
        h, w, c = frame.shape
        label_height=30
        box_width=20
        box_height=20
        label_per_row=4
        label_height=30
        class_ids = [i["class_id"] for i in expected_classes]
        detcetd_class_ids=[ i["class_id"] for i in detected_class]

        label_row = math.ceil(len(list(set(detcetd_class_ids)))/label_per_row)
        label_width = int(frame.shape[1]/label_per_row)
        img_label = np.zeros([label_row*label_height, frame.shape[1],3],dtype=np.uint8)
        img_label.fill(255)
        i = 0
        j = 0
        xgap = 5
        ygap = 5
        unique_class=list(set([i["class_name"] for i in detected_class]))
        unique_class_id=list(set([i["class_id"] for i in detected_class]))
        for cls,idx in zip(unique_class,unique_class_id):
            expected_class = expected_classes[class_ids.index(int(idx))]
            xo,  yo = i*label_width, j*label_height
            bound_color=ImageColor.getcolor(expected_class["bound_color"],"RGB")[::-1]
            text_color=ImageColor.getcolor(expected_class["text_color"],"RGB")[::-1]
            bound_thickness=expected_class["bound_thickness"]
            text_thickness=expected_class["text_thickness"]
            img_label = cv2.rectangle(img_label, (int(xo+xgap), int(yo+ygap)), (int(xo+xgap+box_width), int(yo+ygap+box_height)), bound_color, bound_thickness)
            img_label = cv2.putText(img_label, expected_class["class_name"], (int(xo+box_width+2*xgap), int(yo+ygap+box_height)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color,text_thickness)
            i+=1
            if(i>=label_per_row):
                i=0
                j+=1
        for det in detected_class:
            class_id=det["class_id"]
            expected_class = expected_classes[class_ids.index(int(class_id))]
            bound_color=ImageColor.getcolor(expected_class["bound_color"],"RGB")[::-1]
            text_color=ImageColor.getcolor(expected_class["text_color"],"RGB")[::-1]
            bound_thickness=expected_class["bound_thickness"]
            text_thickness=expected_class["text_thickness"]
            xmin,ymin,xmax,ymax=det["xmin"],det["ymin"],det["xmax"],det["ymax"]
            class_id=det["class_id"]
            
            cv2.rectangle(frame,(xmin, ymin),(xmax,ymax),bound_color,bound_thickness)
            cv2.rectangle(
                    frame,
                    (det["xmin"], det["ymin"]),
                    (det["xmin"] + (det["xmax"] - det["xmin"]), det["ymin"] - 30),
                    bound_color,
                    -1
                )
            if det["class_name"] in det and type(det[det["class_name"]])== type('abc'):
               
                cv2.putText(
                    frame,
                    str(det[det["class_name"]]),
                    (int(det["xmin"]), int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    text_color,
                    thickness=text_thickness
                )
            if "speed" in det:
                cv2.putText(
                    frame,
                    str(det["speed"])+" kmph",
                    (int(det["xmax"])-30, int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    text_color,
                    thickness=text_thickness
                )



            
        image_final = cv2.vconcat([ img_label, frame])

        return image_final

   

    
    def left_legend(self,frame,expected_classes, detected_class):
        h, w, c = frame.shape
        label_height=30
        box_width=10
        box_height=10
        label_per_row=1
        label_height=30
        class_ids = [i["class_id"] for i in expected_classes]
        detcetd_class_ids=[ i["class_id"] for i in detected_class]

        label_row = math.ceil(len(list(set(detcetd_class_ids)))/label_per_row)
        label_width = 60#int(frame.shape[0]/label_per_row)
        img_label = np.zeros([frame.shape[0],150 ,3],dtype=np.uint8)
        img_label.fill(255)
        i = 0
        j = 0
        xgap = 5
        ygap = 5
        print("======left legend======")
        drawn_target=[]
        unique_class=list(set([i["class_name"] for i in detected_class]))
        unique_class_id=list(set([i["class_id"] for i in detected_class]))
        for cls,idx in zip(unique_class,unique_class_id):
            expected_class = expected_classes[class_ids.index(int(idx))]
            xo,  yo = i*label_width, j*label_height
            bound_color=ImageColor.getcolor(expected_class["bound_color"],"RGB")[::-1]
            text_color=ImageColor.getcolor(expected_class["text_color"],"RGB")[::-1]
            bound_thickness=expected_class["bound_thickness"]
            text_thickness=expected_class["text_thickness"]
            img_label = cv2.rectangle(img_label, (int(xo+xgap), int(yo+ygap)), (int(xo+xgap+box_width), int(yo+ygap+box_height)), bound_color, bound_thickness)
            img_label = cv2.putText(img_label, expected_class["class_name"], (int(xo+box_width+2*xgap), int(yo+ygap+box_height)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color,text_thickness)
            i+=1
            if(i>=label_per_row):
                i=0
                j+=1



        for det in detected_class:
            print("======det1======")
            class_id=det["class_id"]
            expected_class = expected_classes[class_ids.index(int(class_id))]
           
            bound_color=ImageColor.getcolor(expected_class["bound_color"],"RGB")[::-1]
            print("====det3====",bound_color)
            text_color=ImageColor.getcolor(expected_class["text_color"],"RGB")[::-1]
            print("====det4====",text_color)
            bound_thickness=expected_class["bound_thickness"]
            print("====det5====",bound_thickness)
            text_thickness=expected_class["text_thickness"]
            print("====det6====",bound_thickness)
            print("====det7======")
            
            
            xmin,ymin,xmax,ymax=det["xmin"],det["ymin"],det["xmax"],det["ymax"]
            class_id=det["class_id"]
            print("====det8======")
            
            cv2.rectangle(frame,(xmin, ymin),(xmax,ymax),bound_color,bound_thickness)
            cv2.rectangle(
                    frame,
                    (det["xmin"], det["ymin"]),
                    (det["xmin"] + (det["xmax"] - det["xmin"]), det["ymin"] - 30),
                    bound_color,
                    -1
                )
        
            if det["class_name"] in det and type(det[det["class_name"]])== type('abc'):
               
                cv2.putText(
                    frame,
                    str(det[det["class_name"]]),
                    (int(det["xmin"]), int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    text_color,
                    thickness=text_thickness
                )
            if "speed" in det:
                cv2.putText(
                    frame,
                    str(det["speed"])+" kmph",
                    (int(det["xmax"])-30, int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    text_color,
                    thickness=text_thickness
                )



            
        image_final = cv2.hconcat([frame, img_label])

        return image_final



    def right_legend(self,frame,expected_classes, detected_class):
        h, w, c = frame.shape
        label_height=30
        box_width=10
        box_height=10
        label_per_row=1
        label_height=30
        class_ids = [i["class_id"] for i in expected_classes]
        detcetd_class_ids=[ i["class_id"] for i in detected_class]

        label_row = math.ceil(len(list(set(detcetd_class_ids)))/label_per_row)
        label_width = 60#int(frame.shape[0]/label_per_row)
        img_label = np.zeros([frame.shape[0],150 ,3],dtype=np.uint8)
        img_label.fill(255)
        i = 0
        j = 0
        xgap = 5
        ygap = 5
        print("======left legend======")
        drawn_target=[]
        unique_class=list(set([i["class_name"] for i in detected_class]))
        unique_class_id=list(set([i["class_id"] for i in detected_class]))
        for cls,idx in zip(unique_class,unique_class_id):
            expected_class = expected_classes[class_ids.index(int(idx))]
            xo,  yo = i*label_width, j*label_height
            bound_color=ImageColor.getcolor(expected_class["bound_color"],"RGB")[::-1]
            text_color=ImageColor.getcolor(expected_class["text_color"],"RGB")[::-1]
            bound_thickness=expected_class["bound_thickness"]
            text_thickness=expected_class["text_thickness"]
            img_label = cv2.rectangle(img_label, (int(xo+xgap), int(yo+ygap)), (int(xo+xgap+box_width), int(yo+ygap+box_height)), bound_color, bound_thickness)
            img_label = cv2.putText(img_label, expected_class["class_name"], (int(xo+box_width+2*xgap), int(yo+ygap+box_height)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color,text_thickness)
            i+=1
            if(i>=label_per_row):
                i=0
                j+=1



        for det in detected_class:
            print("======det1======")
            class_id=det["class_id"]
            expected_class = expected_classes[class_ids.index(int(class_id))]
           
            bound_color=ImageColor.getcolor(expected_class["bound_color"],"RGB")[::-1]
            print("====det3====",bound_color)
            text_color=ImageColor.getcolor(expected_class["text_color"],"RGB")[::-1]
            print("====det4====",text_color)
            bound_thickness=expected_class["bound_thickness"]
            print("====det5====",bound_thickness)
            text_thickness=expected_class["text_thickness"]
            print("====det6====",bound_thickness)
            print("====det7======")
            
            
            xmin,ymin,xmax,ymax=det["xmin"],det["ymin"],det["xmax"],det["ymax"]
            class_id=det["class_id"]
            print("====det8======")
            
            cv2.rectangle(frame,(xmin, ymin),(xmax,ymax),bound_color,bound_thickness)
            cv2.rectangle(
                    frame,
                    (det["xmin"], det["ymin"]),
                    (det["xmin"] + (det["xmax"] - det["xmin"]), det["ymin"] - 30),
                    bound_color,
                    -1
                )
        
            if det["class_name"] in det and type(det[det["class_name"]])== type('abc'):
               
                cv2.putText(
                    frame,
                    str(det[det["class_name"]]),
                    (int(det["xmin"]), int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    text_color,
                    thickness=text_thickness
                )
            if "speed" in det:
                cv2.putText(
                    frame,
                    str(det["speed"])+" kmph",
                    (int(det["xmax"])-30, int(det["ymin"])),
                    cv2.FONT_HERSHEY_SIMPLEX,
                     0.5,
                    text_color,
                    thickness=text_thickness
                )



            
        image_final = cv2.hconcat([ img_label,frame])

        return image_final



    
    def internal_legend(self, frame,expected_classes,detected_class):
        '''
        Annotate internally on image
        Args:
            frame (np.array):  numpy array
        returns:
            frame (np.array):  numpy array
        '''
       
        FONT_SCALE = 0.5
        try:
            # print("====class id====")
            class_ids = [i["class_id"] for i in expected_classes]
            for det in detected_class:
                # print(det)
                x1 = det["xmin"]
                y1 = det["ymin"]
                x2 = det["xmax"]
                y2 = det["ymax"]
                class_name = det["class_name"]
                width = int(x2) - int(x1)
                height = int(y2) - int(y1)
                class_id = det["class_id"]
                expected_class = expected_classes[class_id.index(str(class_id))]

                
                
                frame = cv2.rectangle(
                    frame,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    color=ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                    thickness=expected_class["text_thickness"],
                )
                
                if det["id"] is  None:
                    
                    cv2.rectangle(
                        frame,
                        (int(x1), int(y1)),
                        (int(x1) + (int(x2) - int(x1)), int(y1) - 30),
                        ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                        -1,
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
                        ImageColor.getcolor(expected_class["bound_color"], "RGB")[::-1],
                        -1,
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
                    
                    cv2.putText(
                        frame,
                        str(det[det["class_name"]]),
                        (int((int(x1)+int(x2))/2), int(y1)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5,
                color=ImageColor.getcolor(expected_class["text_color"], "RGB")[::-1],
                thickness=2
                    )
                if "speed" in det:
                    
                    cv2.putText(
                        frame,
                        str(det["speed"])+" kmph",
                        (int(x2)-30, int(y1)),
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

    def annotate(self, legend_state=0,orientation=1):
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
        #frame=self.bottom_legend(frame,expected_classes,detected_class)

        h,w,c=frame.shape
        if len(self.detected_class) > 0:
            
            try:
                if int(legend_state) == 1:
                    if orientation==2:
                    # print("====exter legend====")
                        frame = self.left_legend(frame,expected_classes,detected_class)
                    elif orientation==1:
                        frame = self.right_legend(frame,expected_classes,detected_class)
                    elif orientation==4:
                        frame = self.bottom_legend(frame,expected_classes,detected_class)
                    elif orientation==3:
                        frame = self.top_legend(frame,expected_classes,detected_class)

                    
                        
                else:
                    # print("====internal legend====")
                    frame = self.internal_legend(frame,expected_classes,detected_class)
            except:
                # print("====internal legend exceptions====")
                frame = self.internal_legend(frame,expected_classes,detected_class)
        del self.expected_class, self.detected_class,self.misc_data, misc_data,expected_classes,detected_class
        return frame
