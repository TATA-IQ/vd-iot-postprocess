import cv2
import numpy as np
from datetime import datetime
from PIL import ImageColor
class AnnotateImage():
    def __init__(self, expected_class, detected_class,frame):
        self.expected_class=expected_class
        self.detected_class=detected_class
        self.frame=frame
    
    def create_legend(self):
        h,w,c=self.frame.shape
        legend=np.full(shape=(h,int(0.2*w),c),fill_value=255,dtype=self.frame.dtype)
        return legend

    def external_legend(self,frame):
        h,w,c=frame.shape
        legend=self.create_legend()
        frame=cv2.hconcat([frame,legend])
        totaldetected_class=len(self.detected_class)
        pixeldiff_h,pixeldiff_w,pixeldiff_c= frame.shape
        start_pixel_h=30
        class_ids=[i["class_id"] for i in self.expected_class ]
        start_pixel_w=pixeldiff_w-int(0.2*w)+10
        for det in self.detected_class:
            print("===annot detect===",annot)
            try:
                class_id=det["class_id"]
            except:
                return frame
            expected_class=self.expected_class[class_id.index(str(class_id))]
            
            frame=cv2.putText(frame,det["class_name"],org=(start_pixel_w,start_pixel_h), 
            fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5,color=ImageColor.getcolor(expected_class["text_color"], "RGB"),
            thickness=3)
            #cv2.imwrite("font.jpg",frame)
            
            frame=cv2.circle(frame,( start_pixel_w+70, start_pixel_h-3),5, ImageColor.getcolor(expected_class["bound_color"], "RGB"), cv2.FILLED) 
            frame=cv2.rectangle(frame, (det["xmin"], det["ymin"]), (det["xmax"], det["ymax"]), color=ImageColor.getcolor(expected_class["bound_color"], "RGB"), thickness=expected_class["bound_thickness"])
            start_pixel_h=start_pixel_h+40
        return frame

    def internal_legend(self,frame):
        
        FONT_SCALE = 0.5
        try:
            class_ids=[i["class_id"] for i in self.expected_class ]
        
            for det in self.detected_class:
                x1 = det["xmin"]
                y1 = det["ymin"]
                x2 = det["xmax"]
                y2 = det["ymax"]
                class_name = det["class_name"]
                width =x2 - x1
                height = y2 - y1
                class_id=det["class_id"]
                
                expected_class=self.expected_class[class_id.index(str(class_id))]
                
                #overlap = output[i]["overlap"]
                #print("=======annotation====")
                frame=cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color=ImageColor.getcolor(expected_class["bound_color"],"RGB"), thickness=expected_class["text_thickness"])
                # cv2.rectangle(image, (int(x1), int(y1)), (int(x1)+(int(x2) - int(x1)), int(y1) - 10), color=color_code[class_name],
                #             thickness=-1)
                #print("=====text========")
                frame=cv2.putText(frame, class_name, (int(x1), int(y1)), cv2.FONT_HERSHEY_SIMPLEX, min(width, height) * FONT_SCALE*10, color=ImageColor.getcolor(expected_class["bound_color"],"RGB"), thickness=expected_class["bound_thickness"])
                cv2.imwrite("annot_frame/"+str(datetime.utcnow())+".jpg",frame)
        except Exception as ex:
            print("Exception while annotation===>",ex)
        return frame


    
    def annotate(self,legend_state=0):
        frame=np.copy(self.frame)
        
        #h,w,c=frame.shape
        if int(legend_state)==1:
            frame=self.external_legend(frame)
        else:
            frame=self.internal_legend(frame)
        return frame
        

        


