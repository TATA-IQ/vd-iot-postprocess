class PPETemplate:
    def __init__(self, data):
        print("======Calling PPE Template====")
        self.data = data

        self.expected_classes = [
            "human",
            "vest",
            "novest",
            "helmet",
            "nohelmet",
            "mask",
            "nomask",
            "goggles",
            "nogoggles",
            "shoes",
            "noshoes",
            "earplug",
            "noearplug",
            "harness",
            "noharness",
            "gloves",
            "nogloves",
            "arm",
        ]

    def overlap(self, Xmin, Ymin, Xmax, Ymax, Xmin1, Ymin1, Xmax1, Ymax1):
        if Xmin > Xmax1 or Xmin1 > Xmax or Ymin > Ymax1 or Ymin1 > Ymax:
            ov = 0
        else:
            ov = (max(Xmin, Xmin1) - min(Xmax, Xmax1)) * (max(Ymin, Ymin1) - min(Ymax, Ymax1))
        return round(100 * ov / ((Xmax1 - Xmin1) * (Ymax1 - Ymin1)), 1)

    def check_overlap_classes(self, person_data, data):
        for dt in data:
            if dt["class_name"] in self.expected_classes:
                overlap = self.overlap(
                    person_data["xmin"],
                    person_data["ymin"],
                    person_data["xmax"],
                    person_data["ymax"],
                    dt["xmin"],
                    dt["ymin"],
                    dt["xmax"],
                    dt["ymax"],
                )
                if overlap >= 80:
                    yield dt

    def filter_data(self):
        finalresult = []
        for dt in self.data:
            if dt["class_name"] == "person" or dt["class_name"] == "human":
                finalresult.append(dt)
                for ovr in self.check_overlap_classes(dt, self.data):
                    finalresult.append(ovr)

        return finalresult
