class IncidentExtract:
    def __init__(self, detected_output, incidents, steps):
        # print("======Incident======")
        self.detection_output = detected_output

        if "misc" in self.detection_output:
            self.misc = self.detection_output["misc"]
        else:
            self.misc = None

        self.incident_id = 0
        self.steps = steps
        self.steps_values = list(steps.values())
        print("=====filter steps===")
        # print(self.steps)
        self.derived_steps = list(filter(lambda x: x["step_type"] == "computation", self.steps_values))

        self.incident_keys = list(incidents.keys())
        self.incident_values = list(incidents.values())
        print("=====checking incident=====")
        print(self.incident_values)
        self.incident_class_id = [i["class_id"] for i in self.incident_values]
        self.incident_name = [i["incident_name"] for i in self.incident_values]
        self.incident_id_list = [i["incident_id"] for i in self.incident_values]
        self.incident_class = [i["class_name"] for i in self.incident_values]
        self.incident_type_id = [i["incident_type_id"] for i in self.incident_values]
        self.incident_type_name = [i["incident_type_name"] for i in self.incident_values]

    def vehicle_incident_anpr(self):
        print("====calling base incident===")
        dictwithincidentflag = []
        incidentlist = []

        if "prediction_class" in self.detection_output:
            for dtdata in self.detection_output["prediction_class"]:
                incidentdict = {}
                print("++++++++++", dtdata)
                if dtdata["class_name"] in dtdata and len(dtdata[dtdata["class_name"]]) > 1:
                    print("classname got", dtdata["class_name"])
                    # if dtdata["class_name"] in self.incident_class:
                    incidentdict["incident_no"] = self.incident_id
                    print("#######executed1")
                    incidentdict["incident_id"] = int(
                        self.incident_id_list [self.incident_class.index(dtdata["class_name"])]
                    )
                    print("#####executed2")
                    incidentdict["name"] = self.incident_name[self.incident_class.index(dtdata["class_name"])]
                    print("#####executed3")
                    incidentdict["coordinate"] = {
                        "x1": dtdata["xmin"],
                        "x2": dtdata["xmax"],
                        "y1": dtdata["ymin"],
                        "y2": dtdata["ymax"],
                    }
                    print("#####executed4")
                    incidentdict["misc"] = [{"numberplate": dtdata[dtdata["class_name"]]}]
                    print("=============")
                    print(incidentdict)
                    dtdata["incident_status"] = True
                    self.incident_id = self.incident_id + 1
                    incidentlist.append(incidentdict)
                    dictwithincidentflag.append(dtdata)
                else:
                    dtdata["incident_status"] = False
                    dictwithincidentflag.append(dtdata)
            print("*************Incident list********")
            print(incidentlist)
        else:
            print("-------not exist------")

        return incidentlist, dictwithincidentflag

    def vehicle_incident_svd(self):
        print("====calling base incident===")
        dictwithincidentflag = []
        incidentlist = []
        trackids = []
        if "misc" in self.detection_output:
            trackids = [i["id"] for i in self.detection_output["misc"]]
        if "prediction_class" in self.detection_output:
            for dtdata in self.detection_output["prediction_class"]:
                incidentdict = {}
                print("++++++++++", dtdata)
                if "speed" in dtdata and dtdata["id"] in trackids:
                    print("classname got", dtdata["class_name"])
                    # if dtdata["class_name"] in self.incident_class:
                    incidentdict["incident_no"] = self.incident_id
                    print("#######executed1")
                    incidentdict["incident_id"] = int(
                        self.incident_id_list[self.incident_class.index(dtdata["class_name"])]
                    )
                    print("#####executed2")
                    incidentdict["name"] = self.incident_name[self.incident_class.index(dtdata["class_name"])]
                    print("#####executed3")
                    incidentdict["coordinate"] = {
                        "x1": dtdata["xmin"],
                        "x2": dtdata["xmax"],
                        "y1": dtdata["ymin"],
                        "y2": dtdata["ymax"],
                    }
                    print("#####executed4")
                    incidentdict["misc"] = [{"data": dtdata["speed"], "text": "speed"}]
                    if dtdata[dtdata["class_name"]] in dtdata:
                        incidentdict["misc"].append({"data": dtdata[dtdata["class_name"]], "text": "nuberplate"})
                    print("=============")
                    print(incidentdict)
                    dtdata["incident_status"] = True
                    self.incident_id = self.incident_id + 1
                    incidentlist.append(incidentdict)
                    dictwithincidentflag.append(dtdata)
                else:
                    dtdata["incident_status"] = False
                    dictwithincidentflag.append(dtdata)
            print("*************Incident list********")
            print(incidentlist)
        else:
            print("-------not exist------")

        return incidentlist, dictwithincidentflag

    def base_incident(self):
        print("====calling base incident===")
        dictwithincidentflag = []
        incidentlist = []
        print(self.detection_output)
        if "prediction_class" in self.detection_output:
            for dtdata in self.detection_output["prediction_class"]:
                incidentdict = {}
                if dtdata["class_name"] in self.incident_class:
                    print("======creating incident=======")
                    incidentdict["incident_no"] = self.incident_id
                    incidentdict["incident_id"] = int(
                        self.incident_id_list[self.incident_class.index(dtdata["class_name"])]
                    )
                    incidentdict["name"] = self.incident_name[self.incident_class.index(dtdata["class_name"])]
                    incidentdict["coordinate"] = {
                        "x1": dtdata["xmin"],
                        "x2": dtdata["xmax"],
                        "y1": dtdata["ymin"],
                        "y2": dtdata["ymax"],
                    }
                    incidentdict["misc"] = []
                    dtdata["incident_status"] = True
                    self.incident_id = self.incident_id + 1
                    incidentlist.append(incidentdict)
                    dictwithincidentflag.append(dtdata)
                else:
                    print("class name not found in incident==>", dtdata["class_name"])
                    dtdata["incident_status"] = False
                    dictwithincidentflag.append(dtdata)
        print("*************Incident list********")
        print(incidentlist)

        return incidentlist, dictwithincidentflag

    def base_incident_with_misc(self, step=None):
        print("====calling base incident===")
        dictwithincidentflag = []
        incidentlist = []
        print(self.detection_output)
        if "prediction_class" in self.detection_output:
            for dtdata in self.detection_output["prediction_class"]:
                incidentdict = {}
                if dtdata["class_name"] in self.incident_class:
                    print("======creating incident=======")
                    incidentdict["incident_no"] = self.incident_id
                    incidentdict["incident_id"] = int(
                        self.incident_id_list[self.incident_class.index(dtdata["class_name"])]
                    )
                    incidentdict["name"] = self.incident_name[self.incident_class.index(dtdata["class_name"])]
                    incidentdict["coordinate"] = {
                        "x1": dtdata["xmin"],
                        "x2": dtdata["xmax"],
                        "y1": dtdata["ymin"],
                        "y2": dtdata["ymax"],
                    }
                    if step is not None:
                        upper_limit = float(step["upper_limit"])
                        lower_limit = float(step["lower_limit"])
                        tolerance = float(step["tolerance"])
                        incidentdict["misc"] = []
                        if dtdata["class_name"] in dtdata:
                            upper_limit = float(upper_limit) + (float(tolerance) / 100) * float(upper_limit)
                            lower_limit = float(lower_limit) - (float(tolerance) / 100) * float(lower_limit)
                            if (
                                float(dtdata[dtdata["class_name"]]) < lower_limit
                                or float(dtdata[dtdata["class_name"]]) > upper_limit
                            ):
                                dtdata["incident_status"] = True
                                self.incident_id = self.incident_id + 1
                                print("=====step====")
                                print(step)
                                incidentdict["misc"].append(
                                    {"data": dtdata[dtdata["class_name"]], "text": step["computation_name"]}
                                )
                                incidentlist.append(incidentdict)
                                dictwithincidentflag.append(dtdata)

                    else:
                        if dtdata["class_name"] in dtdata:
                            incidentdict["misc"] = []
                            dtdata["incident_status"] = True
                            self.incident_id = self.incident_id + 1
                            incidentdict["misc"].append({"data": dtdata[dtdata["class_name"]], "text": step["name"]})
                            incidentlist.append(incidentdict)
                            dictwithincidentflag.append(dtdata)
                else:
                    print("class name not found in incident==>", dtdata["class_name"])
                    dtdata["incident_status"] = False
                    dictwithincidentflag.append(dtdata)
        print("*************Incident list********")
        print(incidentlist)

        return incidentlist, dictwithincidentflag

    def create_derived_incident(self, idx, incident_list):
        # incident_list=[]
        incidentdict = {}

        incidentdict["incident_no"] = self.incident_id
        print("*******", idx)
        incidentdict["incident_id"] = int(self.incident_id_list [idx])
        incidentdict["name"] = self.incident_name[idx]
        incidentdict["coordinate"] = {"x1": "", "x2": "", "y1": "", "y2": ""}
        incidentdict["misc"] = incident_list
        self.incident_id = self.incident_id + 1
        return [incidentdict]

    def derived_incident(self, idx, step):
        class_name = self.incident_class[idx]
        icident_value = self.incident_values[idx]
        detected_output = []
        print("====checking derived incidentt====")

        if "prediction_class" in self.detection_output and len(self.detection_output["prediction_class"]) > 0:
            detected_output = self.detection_output["prediction_class"]

        print("======derived incident====")

        upper_limit = float(step["upper_limit"])
        lower_limit = float(step["lower_limit"])
        tolerance = float(step["tolerance"])

        upper_limit = upper_limit + (upper_limit) * (tolerance / 100)
        lower_limit = lower_limit - (lower_limit) * (tolerance / 100)
        incident_list = []
        print("======self misc=====")
        print(self.misc)
        print(class_name)
        if class_name is None:
            if self.misc is not None or len(self.misc) > 0:
                for i in self.misc:
                    val = i["data"]
                    text = i["text"]
                    if val >= upper_limit or val <= lower_limit:
                        incident_list.append({"data": val, "text": text})

            if len(incident_list) > 0:
                return self.create_derived_incident(idx, incident_list), detected_output
            else:
                return [], detected_output
        else:
            incident_list, detected_output = self.base_incident_with_misc(step)
            return incident_list, detected_output

    def process_incident(self):
        incidentlist, detectin_incidentflag = [], []
        print("=====parent class incident====")
        print("************incident type*******")
        print(self.incident_type_id)
        if 1 in self.incident_type_id:
            tempincidentlist, temp_detectionlist = self.base_incident()
            incidentlist.extend(tempincidentlist)
            detectin_incidentflag.extend(temp_detectionlist)

        print("======checking incident type id=====")
        print(self.incident_type_id)
        print(self.derived_steps)
        for idx, inc_id in enumerate(self.incident_type_id):
            if int(inc_id) == 2:
                for st in self.derived_steps:
                    tempderived_incident, detectin_incidentflag = self.derived_incident(idx, st)
                    print("====incidebts====")
                    print(tempderived_incident)
                    if len(tempderived_incident) > 0:
                        incidentlist.extend(tempderived_incident)
        print("=====Returning=====")
        return incidentlist, detectin_incidentflag
