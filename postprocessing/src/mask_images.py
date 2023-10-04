import cv2
import numpy as np
class Maskingself.frame():
    def __init__(self,frame,mask,usecase_id,camera_id,detected_output):
        self.usecase_id=usecase_id
        self.camera_id=camera_id
        self.mask=mask
        self.frame=frame
    def mask_creation(self): 
        '''
        only for png self.frame
        '''

        b,g,r,a = cv2.split(self.frame)
        a[a>0] = 1
        mask = a
        return mask 
    def background_creation( self,mask): #this is use to create yellow colored space for Intrusion area
        b,g,r,a = cv2.split(self.frame)
        mask_array = mask.reshape((mask.shape[0],mask.shape[1],1))
        self.frame_b = np.ones([self.frame.shape[0], self.frame.shape[1],1], dtype=np.uint8)
        self.frame_g= np.ones([self.frame.shape[0], self.frame.shape[1],1], dtype=np.uint8)
        self.frame_r= np.ones([self.frame.shape[0], self.frame.shape[1],1], dtype=np.uint8)
        self.frame_b = 0*self.frame_b
        self.frame_g = 255*self.frame_g*mask_array
        self.frame_r = 255*self.frame_r*mask_array
        img_bgr = cv2.merge((self.frame_b,self.frame_g,self.frame_r))
        return img_bgr

    def process_mask(self):
        frame_back = cv2.resize(self.frame_back, (self.frame.shape[1], self.frame.shape[0]), interpolation = cv2.INTER_AREA)
        mask = cv2.resize(mask, (self.frame.shape[1], self.frame.shape[0]), interpolation = cv2.INTER_AREA)
        mask = mask.reshape((mask.shape[0],mask.shape[1],1))
        self.frame= cv2.addWeighted(self.frame, alpha, self.frame_back, 1 - alpha, 0)
        return self.frame, mask
        

