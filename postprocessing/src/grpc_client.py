import grpc
import numpy as np
from grpc_protos import trackgrpc_pb2, trackgrpc_pb2_grpc


class GRPCClient(object):
    """
    GRPC Client for Encoder image in Tensorflow
    """

    def __init__(self):
        self.host = "localhost"
        self.server_port = 50051

        # instantiate a channel
        self.channel = grpc.insecure_channel("{}:{}".format(self.host, self.server_port))

        # bind the client and the server
        self.stub = trackgrpc_pb2_grpc.trackStub(self.channel)

    def get_url(self, message):
        """
        Client function to call the rpc for GetServerResponse
        """
        # "usecase_id":usecase_id,"cameraid":cameraid,"bboxes":bboxes
        # {"usecase_id":usecase_id,"cameraid":cameraid,"image":frame,"bboxes":bboxes}
        # ,bboxes=[message["bboxes"].tolist()[0]]
        # print("=====GRPC Calling===")
        # print(type(message["usecase_id"]))
        # print(type(message["cameraid"]))
        # print(type(message["image"]))
        # print("====bboxes====")
        # print("shape====",message["bboxes"])
        message = trackgrpc_pb2.TrackRequest(
            usecase_id=str(message["usecase_id"]),
            cameraid=str(message["cameraid"]),
            image=message["image"],
            bbox=message["bboxes"].tobytes(),
        )

        message_val = self.stub.gettrack(message)

        feature = np.frombuffer(message_val.feature, dtype=np.float32)
        feature = np.array(feature).reshape(int(len(feature) / 128), 128)
        # print("===feature shape====")
        # print(feature.shape)
        # newfeature=[i[0] for i in feature ]
        # newfeature=np.array(newfeature).reshape(int( len(newfeature)/128),128)
        return message_val.usecase_id, message_val.cameraid, feature
