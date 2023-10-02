import redis
class Caching():
    def __init__(self,rcon):
        self.rcon=rcon
    
    def setbykey(self,camera_id, usecase_id,data):
        self.rcon.set(str(camera_id)+"_"+str(usecase_id),data)
    def getbykey(self,camera_id, usecase_id):
        return self.rcon.get(str(camera_id)+"_"+str(usecase_id))

