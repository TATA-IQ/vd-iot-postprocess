"""
Caching
"""
import json


class Caching:
    '''
    Save and get detection to/from cache
    '''
    def __init__(self, rcon):
        """
        Create connection with local cache
        Args:
            rcon (object): redis connection
        """
        # print("====initializing cache===")
        self.rcon = rcon
        # print("=====Initialization cache done===")

    def setbykey(self, key, camera_id, usecase_id, data):
        """
        Save data to cache
        Args:
            key (str): predifine key based on template
            camera_id (int or str): camera id
            usecase_id (int or str): usecase id
            data (dict): detection data
        """
        try:
            print("=====cache storing===")
            self.rcon.set(key + "_" + str(camera_id) + "_" + str(usecase_id), json.dumps(data), ex=60)
            print("========cache stored=========")
        except Exception as ex:
            print("exception while saving: ", ex)

    def getbykey(self, key, camera_id, usecase_id):
        """
        Get data from cache
        Args:
            key (str): predifine key based on template
            camera_id (int or str): camera id
            usecase_id (int or str): usecase id
        returns:    
            data (dict): detection data
        """
        cachedata = self.rcon.get(key + "_" + str(camera_id) + "_" + str(usecase_id))
        if cachedata is None:
            return None
        else:
            return json.loads(cachedata)
