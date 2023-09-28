from src.detectionclass import DetectionProcess
from src.annotation import AnnotateImage
class CrowdTemplate(DetectionProcess,AnnotateImage):
    def __init__(self,detected_class,expected_class,frame):
        DetectionProcess.__init__(self,detected_class,expected_class)
    def process_data(self):
        filtered_res=self.process()
        AnnotateImage.__init__(self,detected_class,expected_class)
        image=self.annotate()
        return filtered_res,image



