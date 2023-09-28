class DetectionProcess():
    def __init__(self,detected_class, expected_class):
        self.detected_class=detected_class
        self.expected_class=expected_class

    def process(self):
        uploaded_class_name_list=[self.expected_class[i]["uploaded_class_name"] for i in self.expected_class]
        uploaded_class_name_id= [self.expected_class[i]["class_id"] for i in self.expected_class]
        listresult=[]
        #print("========")
        #print(self.expected_class)
        print("======Uploaded class=====")
        print(uploaded_class_name_list)
        for detc in self.detected_class:
            
            if detc["class_name"] in uploaded_class_name_list:
                print("*******",detc)
                idofclass = str(uploaded_class_name_id[uploaded_class_name_list.index(detc["class_name"])])
                expected_class=self.expected_class[idofclass]
                print(detc["score"],expected_class["class_conf"])
                if detc["score"]>=expected_class["class_conf"]:
                    detc["class_name"]=expected_class["class_name"]
                    detc["class_id"] = str(expected_class["class_id"])
                    listresult.append(detc)
        return listresult


