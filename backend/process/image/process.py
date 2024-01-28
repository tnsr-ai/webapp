import sys

sys.path.append("...")
import os
import replicate
import requests
from utils import USER_TIER

modelsList = {
    "super_resolution": {
        "model": "amitalokbera/imagesr:a3ec50b931c85d7f1eadf474e6a05b2ebbfd7391aea87d3c74e1b569d7dfe125",
    },
    "image_deblurring": {
        "model": "amitalokbera/imagedeblurring:0b1b4e8d744354423ac80b029567f81f141e4839bfffc62e1b900a61229da4f6"
    },
    "image_denoising": {
        "model": "amitalokbera/imagedenoising:d8fd15077b9d1ea68767fe9d78c14b1ccf8febcf1d18d8028f7d21f1a1b337cb"
    },
    "remove_background": {
        "model": "amitalokbera/removebg:e26324a8420dd2bf06ebe1e64d6c499354a77a777e4f7bab16a5146a917171bc"
    },
    "face_restoration": {
        "model": "amitalokbera/facerestoration:919e0bb5def613331fe968ed3cb2cba2e25acd75c5b134e0bbf0ea1bc1cbda62"
    },
    "bw_to_color": {
        "model": "amitalokbera/imagecolorizer:557257df2b4895a2c517538e5482ff48552b968cb381e764d9f39a5f72e37d28"
    },
}


class ImageProcess:
    def __init__(self, image_path, filter_config):
        self.image_path = image_path
        self.filter_config = filter_config
        self.output = None
        self.modelList = modelsList
        self.seed = 1999

    def run(self):
        for model_key, config in self.filter_config.items():
            model_name = self.modelList[model_key]["model"]
            model_config = config
            input_path = None
            if self.output is None:
                input_path = self.image_path
            else:
                input_path = self.output
            if model_config["active"]:
                input_config = {}
                if model_key == "super_resolution":
                    input_config = {
                        "image": input_path,
                        "model_name": config["model"],
                        "seed": self.seed,
                    }
                else:
                    input_config = {
                        "image": input_path,
                        "seed": self.seed,
                    }
                self.output = replicate.run(model_name, input=input_config)
        return self.output
