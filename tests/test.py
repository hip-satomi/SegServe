import unittest
import os


class TestSegmentation(unittest.TestCase):

    def setUp(self):
        # download the image
        import requests

        url = 'https://fz-juelich.sciebo.de/s/wAXbC0MoN1G3ST7/download'
        r = requests.get(url, allow_redirects=True)

        print(len(r.content))

        with open('test.png', 'wb') as file:
            file.write(r.content)

    def test_standard(self):
        CI_JOB_TOKEN = os.environ['CI_JOB_TOKEN']

        # test entrypoints: main (Cellpose)
        service_url = 'batch-image-prediction'
        method_repo = f'https://gitlab-ci-token:{CI_JOB_TOKEN}@jugit.fz-juelich.de/mlflow-executors/cellpose-executor.git'

        self.predict(service_url, method_repo, 'main', 'main')
        self.predict(service_url, method_repo, 'omnipose', 'main')

    def predict(self, service_url, method_repo, entrypoint, version):
        import requests
        from io import BytesIO
        from PIL import Image
        import json

        contours = []

        image = Image.open('test.png')

        # convert image into a binary png stream
        byte_io = BytesIO()
        image.save(byte_io, "png")
        byte_io.seek(0)

        # pack this into form data
        multipart_form_data = [
            ("files", ("data.png", byte_io, "image/png"))
        ]

        additional_parameters = {}

        # exactly request segmentation with the current repo version
        params = dict(
            repo=method_repo,
            entry_point=entrypoint,
            version=version,
            parameters=json.dumps(additional_parameters),
        )

        # send a request to the server
        response = requests.post(
            f'http://segserve/{service_url}/', params=params, files=multipart_form_data, timeout=60*60
        )

        # output response
        print(response.content)

        # the request should be successful
        self.assertTrue(response.status_code == 200)

if __name__ == '__main__':
    unittest.main()
