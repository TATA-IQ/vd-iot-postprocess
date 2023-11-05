import copy
from io import BytesIO

import cv2
import imutils
import numpy as np
from PIL import Image
from src.cache import Caching
import pandas as pd
from PIL import ImageColor


class Masking:
    def __init__(self, frame, usecase_id, camera_id, usecase_template_id, rcon=None):
        self.usecase_id = usecase_id
        self.camera_id = camera_id
        
        self.frame = frame
        self.rcon = rcon
        self.alpha = 0.9
        self.usecase_template_id = usecase_template_id

    def convert_image(self, image_str):
        try:
            stream = BytesIO(image_str.encode("ISO-8859-1"))
        except Exception as ex:
            stream = BytesIO(image_str.encode("utf-8"))

        image = Image.open(stream).convert("RGB")

        imagearr = np.array(image)
        return imagearr

    def mask_creation(self, mask_image):
        """
        only for png self.frame
        """

        b, g, r = cv2.split(mask_image)
        r[r > 0] = 1
        mask = r
        return mask

    def background_creation(
        self, mask_image, mask_created
    ):  # this is use to create yellow colored space for Intrusion area
        b, g, r,a= cv2.split(mask_image)
        mask_array = mask_created.reshape((mask_created.shape[0], mask_created.shape[1], 1))
        mask_image_b = np.ones([mask_image.shape[0], mask_image.shape[1], 1], dtype=np.uint8)
        mask_image_g = np.ones([mask_image.shape[0], mask_image.shape[1], 1], dtype=np.uint8)
        mask_image_r = np.ones([mask_image.shape[0], mask_image.shape[1], 1], dtype=np.uint8)
        mask_image_b = 0 * mask_image_b
        mask_image_g = 255 * mask_image_g * mask_array
        mask_image_r = 255 * mask_image_r * mask_array
        img_bgr = cv2.merge((mask_image_b, mask_image_g, mask_image_r))
        return img_bgr

    def get_mask_boundary(self, boundary_config):
        print("======Mask Crating from boundary=====")
        keys=list(boundary_config.keys())
        print("===keys=====")
        width=int(boundary_config[keys[0]]["image_width"])
        height= int(boundary_config[keys[0]]["image_height"])
        print("====width height=====>",width,height)
        img = np.zeros((height,width,3), dtype=np.uint8)
        img_new=None
        
        for gid in keys:
            dfs=pd.DataFrame()
            x=boundary_config[gid]["boundary_coordinates"]["x"]
            y=boundary_config[gid]["boundary_coordinates"]["y"]
            dfs["x"]=x
            dfs["y"]=y
            color=x=boundary_config[gid]["color"]
            img = cv2.fillPoly(img, pts =np.array([np.array(dfs[['x','y']].astype(int))]), color=ImageColor.getcolor(color,"RGB")[::-1])
            #img = cv2.fillPoly(img, pts =np.array([np.array(dfs[['x','y']].astype(int))]), color=(0,255,0))
        return img
    

    def get_mask(self,boundary_config):
        print("======Mask Crating=====")
        mask_image=self.get_mask_boundary(boundary_config)
        # cv2.imwrite("mask1.png",mask_image)
        # mask_image = cv2.cvtColor(mask_image, cv2.COLOR_BGR2RGBA)
        # cv2.imwrite("mask2.png",mask_image)
        print("========mask created=========")
        mask_created = self.mask_creation(mask_image)
        print("========mask created 2=====")
        # cv2.imwrite("mask3_0.png",mask_created*255)
        #image_back = self.background_creation(mask_image, mask_created)
        # cv2.imwrite("mask3.png",mask_created)
        # cv2.imwrite("mask3_1.png",image_back)

        return mask_image,mask_created

    def process_mask(self,boundary_config):
        # cache = Caching(self.rcon)
        # mask = cache.getbykey("mask", self.camera_id, self.usecase_id)
        print("====Processing Mask======")
        mask_image,mask_created = self.get_mask(boundary_config)
        # cv2.imwrite("mask4.png", mask_created)
        image_back = cv2.resize(mask_image, (self.frame.shape[1], self.frame.shape[0]), interpolation = cv2.INTER_AREA)
        # cv2.imwrite("mask_5.png", mask_created)
        # cv2.imwrite("mask_6.png", image_back)
        image = cv2.addWeighted(self.frame, self.alpha, image_back, 1 - self.alpha, 0)
        print("======saving image=====")
        # cv2.imwrite("test.jpg", image)
        return image, image

    
    # def get_mask(self):
    #     print("================Template id===========", self.usecase_template_id)
    #     if int(self.usecase_template_id) == 9:
    #         mask_image = cv2.imread("mask_image_png/pathway_mask.png", cv2.IMREAD_UNCHANGED)
    #         print("=====Mask Read for dedicated pathway======")
    #     if int(self.usecase_template_id) == 11:
    #         mask_image = cv2.imread("mask_image_png/intrusion_mask.png", cv2.IMREAD_UNCHANGED)
    #         print("=====Mask Read for Intrusion======")

    #     mask_image = cv2.cvtColor(mask_image, cv2.COLOR_BGR2RGBA)
    #     mask_created = self.mask_creation(mask_image)
    #     image_back = self.background_creation(mask_image, mask_created)
    #     # cv2.imwrite("mask3.png",mask_created)
    #     return image_back, mask_created

    # def process_mask(self):
    #     cache = Caching(self.rcon)
    #     mask = cache.getbykey("mask", self.camera_id, self.usecase_id)

    #     if mask is not None:
    #         if self.mask_key != mask["key"]:
    #             image_back, mask_created = self.get_mask()
    #             dictmask = {}
    #             dictmask["key"] = self.mask_key
    #             print("=====imageback", image_back.shape)
    #             print("=====imageback", mask_created.shape)
    #             image_back = cv2.resize(
    #                 image_back, (self.frame.shape[1], self.frame.shape[0]), interpolation=cv2.INTER_AREA
    #             )
    #             mask_created = cv2.resize(
    #                 mask_created, (self.frame.shape[1], self.frame.shape[0]), interpolation=cv2.INTER_AREA
    #             )
    #             print("=======", mask_created.shape)
    #             # error on this line
    #             mask_created = mask_created.reshape((mask_created.shape[0], mask_created.shape[1], 1))

    #             dictmask["image_back"] = (
    #                 cv2.imencode(".png", copy.deepcopy(image_back))[1].tobytes().decode("ISO-8859-1")
    #             )
    #             dictmask["mask_created"] = (
    #                 cv2.imencode(".png", copy.deepcopy(mask_created))[1].tobytes().decode("ISO-8859-1")
    #             )
    #             print("===saving in cache====")

    #             cache.setbykey("mask", self.camera_id, self.usecase_id, dictmask)
    #         else:
    #             image_back = self.convert_image(mask["image_back"])
    #             mask_created = self.convert_image(mask["mask_created"])
    #             print("==got it from cavhe===")
    #     else:
    #         image_back, mask_created = self.get_mask()
    #         dictmask = {}
    #         dictmask["key"] = self.mask_key
    #         print("=====imageback", image_back.shape)
    #         print("=====imageback", mask_created.shape)
    #         image_back = cv2.resize(
    #             image_back, (self.frame.shape[1], self.frame.shape[0]), interpolation=cv2.INTER_AREA
    #         )
    #         mask_created = cv2.resize(
    #             mask_created, (self.frame.shape[1], self.frame.shape[0]), interpolation=cv2.INTER_AREA
    #         )
    #         print("=======", mask_created.shape)
    #         # error on this line
    #         mask_created = mask_created.reshape((mask_created.shape[0], mask_created.shape[1], 1))

    #         dictmask["image_back"] = cv2.imencode(".png", copy.deepcopy(image_back))[1].tobytes().decode("ISO-8859-1")
    #         dictmask["mask_created"] = (
    #             cv2.imencode(".png", copy.deepcopy(mask_created))[1].tobytes().decode("ISO-8859-1")
    #         )
    #         print("===saving in cache====")

    #         cache.setbykey("mask", self.camera_id, self.usecase_id, dictmask)

            # call for updated mask
        print("from cache===>", mask_created.shape)
        print("from cache===>", image_back.shape)
        cv2.imwrite("mask4.png", mask_created)
        # image_back = cv2.resize(image_back, (self.frame.shape[1], self.frame.shape[0]), interpolation = cv2.INTER_AREA)
        # mask_created = cv2.resize(mask_created, (self.frame.shape[1], self.frame.shape[0]), interpolation = cv2.INTER_AREA)
        # print("=======",mask_created.shape)
        # #error on this line
        # mask_created = mask_created.reshape((mask_created.shape[0],mask_created.shape[1],1))
        cv2.imwrite("mask_5.png", mask_created)
        image = cv2.addWeighted(self.frame, self.alpha, image_back, 1 - self.alpha, 0)
        print("======saving image=====")
        cv2.imwrite("image/test.jpg", image)
        return image, mask_created


# Test

# import redis
# frame=cv2.imread("/home/aditya.singh10/gitdev/postprocessing/vd-iot-postprocessing/postprocessing/input/1_2023_10_06_05_18_06_253710.jpg", cv2.IMREAD_UNCHANGED)
# pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
# r_con = redis.Redis(connection_pool=pool)
# msk=Masking(frame,"key_dedicated_pathway_2",8,1,r_con)
# image,mask=msk.process_mask()
# print("======save image=====")
# cv2.imwrite("image.jpg",image)
# cv2.imwrite("mask6.png",mask)
