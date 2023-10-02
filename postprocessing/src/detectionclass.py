class DetectionProcess():
    def __init__(self,detected_class, expected_class):
        self.detected_class=detected_class
        self.expected_class=expected_class
    
    

    def process_detection(self):
        
        uploaded_class_name_list=[i["uploaded_class_name"] for i in self.expected_class]
        uploaded_class_name_id= [i["class_id"] for i in self.expected_class]
        
        listresult=[]
        print("====expected class====")
        print(self.expected_class)
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
                    listresult.append(detc)
        # print("====end of detectec class======")
        return listresult


