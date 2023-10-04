import redis
import json
class Caching():
    def __init__(self,rcon):
        #print("====initializing cache===")
        self.rcon=rcon
        #print("=====Initialization cache done===")
    
    def setbykey(self,key,camera_id, usecase_id,data):
        try:
            
            self.rcon.set(key+"_"+str(camera_id)+"_"+str(usecase_id),json.dumps(data))
        except Exception as ex:
            print("exception while saving: ",ex)
    def getbykey(self,key,camera_id, usecase_id):
        cachedata=self.rcon.get(key+"_"+str(camera_id)+"_"+str(usecase_id))
        if cachedata is None:
            return None
        else:
            return json.loads(cachedata)

