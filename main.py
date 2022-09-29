from shutil import Error
from typing import List, Optional
from furl import furl

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics
from prometheus_client import start_http_server, Summary, Histogram, Counter, Info

# Create a metric to track via prometheus

# track cell count that comes out of segmentation
labels = ['method_repo', 'entrypoint', 'version', 'parameters']
prom_segmentation_cell_count = Histogram('segmentation_cells', 'Time spent processing request', labels, buckets=[10, 20, 40, 80, 120, 200, 400, 600, 800, 1200, 1600, 2000, 2500, 3000, 4000, float('inf')])
# track the total segmentation time in seconds
prom_segmentation_seconds = Histogram('segmentation_seconds', 'Time spent processing request', labels, buckets=(1., 3., 6., 9., 12, 16., 20., 30., 40., 50., 60., 90., 120, 150, 180, 240, 300, float('inf')))
# track the segmentation time per image
prom_segmentation_per_image_seconds = Histogram('segmentation_per_image_seconds', 'Time spent processing request', labels, buckets=(1., 3., 6., 9., 12, 16., 20., 30., 40., 50., 60., 90., 120, 150, 180, 240, 300, float('inf')))
# track the number of images
prom_segmentation_images = Counter('segmenation_images', 'Number of segmented images', labels)

from utils import TempFolder
import os.path as osp
import mlflow
import json
import logging
import os
import time
from influx import influxdb_report_images, influxdb_report_timing
import traceback

app = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/image-prediction/")
async def image_prediction(repo: str, entry_point: Optional[str] = 'main', version: Optional[str] = 'main', file: UploadFile = File(...), parameters: Optional[str] = None):

    # make a password less repo url for logging
    parsed = furl(repo)
    parsed.password = ""
    parsed.username = ""
    repo_safe = parsed.url

    # write file to temporary folder
    with TempFolder() as tmpDir:

        # write image file
        input_file = osp.join(tmpDir.root, 'input.png')
        output_file = osp.join(tmpDir.root, 'output.json')

        with open(input_file, 'wb') as output:
            output.write(file.file.read())

        additional_parameters = {}
        if parameters:
            try:
                additional_parameters = json.loads(parameters)
            except:
                logging.warning('Failed parsing additional parameters')

        # execute the project
        run = mlflow.projects.run(
            repo,
            entry_point=entry_point,
            version=version,
            backend='local',
            storage_dir=tmpDir.root,
            parameters={
                'input_images': osp.abspath(input_file),
                **additional_parameters
            })

        print(run.run_id)

        # download the output artifact
        client = mlflow.tracking.MlflowClient()
        client.download_artifacts(run.run_id, 'output.json', tmpDir.root)

        if not osp.isfile(output_file):
            raise FileNotFoundError('Could not find "output.json" file. Please log this as an artifact in your code: mlflow.log_artifact(\'output.json\')')

        # just a single image
        prom_segmentation_images.labels(repo_safe, entry_point, version, parameters).inc()

        # collect the results
        with open(output_file, 'r') as output_json:
            result = json.load(output_json)
            result['filename'] = file.filename
            return result

@app.post("/batch-image-prediction/")
async def batch_image_prediction(repo: str, entry_point: Optional[str] = 'main', version: Optional[str] = 'main', files: List[UploadFile] = File(...), parameters: Optional[str] = None, username: Optional[str] = None):
    """Batch image segmentation for multiple image files

    Args:
        repo (str): git url to the repo containing mlflow project with segmentation
        entry_point (Optional[str], optional): mlproject entry point. Defaults to 'main'.
        version (Optional[str], optional): Commit hash/branch/tag of the git repo. Defaults to 'main'.
        files (List[UploadFile], optional): List of image files. Defaults to File(...).
        parameters (Optional[str], optional): Additional parameters to pass on to the repo segmentation approach. Defaults to None.
        username (Optional[str], optional): Information about the requesting user (for metrics only)

    Returns:
        [List]: python list of segmentation results for every image
    """

    # make a password less repo url for logging
    parsed = furl(repo)
    parsed.password = ""
    parsed.username = ""
    repo_safe = parsed.url

    # write file to temporary folder
    with TempFolder() as tmpDir:

        image_paths = []
        output_file = osp.join(tmpDir.root, 'output.json')
        image_folder = osp.join(tmpDir.root, 'images')
        os.makedirs(image_folder)
        for i,file in enumerate(files):
            # write image file
            input_file = osp.join(image_folder, 'i%03d.png' % i)

            image_paths.append(osp.abspath(input_file))

            with open(input_file, 'wb') as output:
                output.write(file.file.read())

        additional_parameters = {}
        if parameters:
            try:
                additional_parameters = json.loads(parameters)
            except:
                logging.warning('Failed parsing additional parameters')

        # execute the project
        current_time = time.time()
        run = mlflow.projects.run(
            repo,
            entry_point=entry_point,
            version=version,
            backend='local',
            storage_dir=tmpDir.root,
            parameters={
                'input_images': image_folder,
                **additional_parameters
            })

        # notify segmentation time
        duration = time.time() - current_time
        prom_segmentation_seconds.labels(repo_safe, entry_point, version, parameters).observe(duration)

        print(run.run_id)

        # download the output artifact
        client = mlflow.tracking.MlflowClient()
        client.download_artifacts(run.run_id, 'output.json', tmpDir.root)

        if not osp.isfile(output_file):
            raise FileNotFoundError('Could not find "output.json" file. Please log this as an artifact in your code: mlflow.log_artifact(\'output.json\')')

        # collect the results
        with open(output_file, 'r') as output_json:
            result = json.load(output_json)
            num_objects = 0
            num_images = len(result['segmentation_data'])

            objects_in_images = []

            # sum the detection counts for all images
            for image_result in result['segmentation_data']:
                num_objects += len(image_result)
                objects_in_images.append(len(image_result))

            # notify influxdb
            try:
                influxdb_report_images(objects_in_images, repo=repo, entry_point=entry_point, version=version, username=username)
                influxdb_report_timing(duration, num_objects, num_images, repo=repo, entry_point=entry_point, version=version, username=username)
            except Exception:
                logging.error("Error while reporting influx data")
                logging.error(traceback.format_exc())

            prom_segmentation_images.labels(repo_safe, entry_point, version, parameters).inc(amount=num_images)
            prom_segmentation_per_image_seconds.labels(repo_safe, entry_point, version, parameters).observe(duration / num_images)
            prom_segmentation_cell_count.labels(repo_safe, entry_point, version, parameters).observe(num_objects)

            return result

    # loop over files
    # perform image prediction for every file
    #results = await image_prediction(repo, entry_point, version, files, parameters)
    #return results


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app",host='0.0.0.0', port=4557, reload=True, debug=True, workers=3)
