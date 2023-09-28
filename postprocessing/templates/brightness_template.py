from PIL import Image, ImageStat
import cv2
import numpy as np
import math
class BrightnessTemplate():
    def __init__(self):
        pass
    def percieved_brightness(self, frame ):
        im=Image.fromarray(frame)
        
        stat = ImageStat.Stat(im)
        b,g,r = stat.rms
        return math.sqrt(0.241*(r**2) + 0.691*(g**2) + 0.068*(b**2))
    def brightness(self,frame):
        frame=cv2.cvtColor(frame, cv2.COLOR_BGR2HSV )
        h,s,v=cv2.split(frame)
        
        return np.mean(v)
    def process_template(self,frame):
        percvd_bright=self.percieved_brightness(frame)
        hsv_bright=self.brightness(frame)
        
        return {"class_name":"brightness","value":percvd_bright}, {"class_name":"brightness","value":hsv_bright}



