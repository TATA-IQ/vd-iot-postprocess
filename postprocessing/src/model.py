import requests


class Model:
    def __init__(self, url, requestparams):
        self.url = url
        self.requestparams = requestparams

    def api_call(self):
        # self.model_urls.append(url)
        try:
            response = requests.post(self.url, json=self.requestparams)
            # current_time=datetime.utcnow()

            # time_diff=(current_time-self.image_time).total_seconds()
            # self.logger.info(f"{self.usecase_id}, {self.camera_id}, model response time, {time_diff}")
            print("=====model result=====")
            print(response.json())
            return response
        except Exception as ex:
            print("=====url======", self.url)
            print("====model call exception====", ex)
            # print(self.requestparams)
            return None
