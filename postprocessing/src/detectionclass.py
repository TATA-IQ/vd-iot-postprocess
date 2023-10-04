class DetectionProcess():
    def __init__(self,detected_class, expected_class,image_time):
        self.detected_class=detected_class
        self.expected_class=expected_class
        self.image_time=image_time
    
    

    def process_detection(self):
        
        uploaded_class_name_list=[i["uploaded_class_name"] for i in self.expected_class]
        uploaded_class_name_id= [i["class_id"] for i in self.expected_class]
        
        listresult=[]
        # print("====expected class====")
        # print(self.expected_class)
        for detc in self.detected_class:
            
            if detc["class_name"] in uploaded_class_name_list:
                # print("*******",detc)
                idofclass = uploaded_class_name_list.index(detc["class_name"])
                # print("index of class===>",idofclass)
                expected_class=self.expected_class[int(idofclass)]
                # print(detc["score"],expected_class["class_conf"])
                if detc["score"]>=expected_class["class_conf"]:
                    detc["class_name"]=expected_class["class_name"]
                    detc["class_id"] = str(expected_class["class_id"])
                    detc["image_time"]=str(self.image_time)
                    listresult.append(detc)
        # print("====end of detectec class======")
        return listresult
    
    def masked_detection(self,image,mask,detections):
        masked_detection=[]
        for det in detections:
            xmin_l, ymin_l, xmax_l, ymax_l = int(detclass['xmin']), int(detclass['ymax']) - int(0.1*(int(detclass['ymax'])-int(detclass['ymin']))), int(detclass['xmax']), int(detclass['ymax'])
            print('lecord:'+str(xmin_l)+', '+str(ymin_l)+', '+str(xmax_l)+', '+str(ymax_l))
            leg_area = np.array([[xmin_l,ymin_l], [xmin_l,ymax_l], [xmax_l, ymax_l], [xmax_l,ymin_l]])
            image_new = np.zeros([image.shape[0],image.shape[1],1],dtype=np.uint8)
            image_new = cv2.fillPoly(image_new, pts =[leg_area], color=(255,255,255))
            img_final = image_new*mask  #cv2.bitwise_and(image_new, image_new, mask=mask)
            count = np.count_nonzero(img_final>0)
            count_pc = 100*count/((xmax_l-xmin_l)*(ymax_l-ymin_l))
            det["overlaped"]=count_pc
            masked_detection.append(det)
        return masked_detection


