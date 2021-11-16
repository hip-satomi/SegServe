from shutil import Error
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile

from utils import TempFolder
import os.path as osp
import mlflow
import json
import logging

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/files/")
async def create_file(file: bytes = File(...)):
    return {"file_size": len(file)}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):

    # write file to temporary folder
    with TempFolder() as tmpDir:

        # write image file
        input_file = osp.join(tmpDir.root, 'input.png')
        output_file = osp.join(tmpDir.root, 'output.json')

        with open(input_file, 'wb') as output:
            output.write(file.file.read())

        # execute the project
        run = mlflow.projects.run(
            'https://gitlab+deploy-token-1:jzCPzEwRQacvqp8z2an9@jugit.fz-juelich.de/mlflow-executors/test-executor.git',
            entry_point='main',
            version='main',
            backend='local',
            storage_dir=tmpDir.root,
            parameters={
                'data_file': osp.abspath(input_file),
                'output_file': osp.abspath(output_file)
            })

        print(run.run_id)

        # download the output artifact
        client = mlflow.tracking.MlflowClient()
        client.download_artifacts(run.run_id, output_file, tmpDir.root)

        if not osp.isfile(output_file):
            raise FileNotFoundError('Could not find "output.json" file. Please log this as an artifact in your code: mlflow.log_artifact(\'output.json\')')

        # collect the results
        with open(output_file, 'r') as output_json:
            return json.load(output_json)


    return {"filename": file.filename}


@app.post("/prediction/")
async def prediction(file: UploadFile = File(...)):

    # write file to temporary folder
    with TempFolder() as tmpDir:

        # write image file
        input_file = osp.join(tmpDir.root, 'input.png')
        output_file = osp.join(tmpDir.root, 'output.json')

        with open(input_file, 'wb') as output:
            output.write(file.file.read())

        # execute the project
        run = mlflow.projects.run(
            'https://gitlab+deploy-token-1:jzCPzEwRQacvqp8z2an9@jugit.fz-juelich.de/mlflow-executors/mmdetection-executor.git',
            entry_point='main',
            version='main',
            backend='local',
            storage_dir=tmpDir.root,
            parameters={
                'input_image': osp.abspath(input_file),
                'config': osp.abspath(osp.join(tmpDir.root, 'sharedData', 'htc_like_def_detr_tuned.py')),
                'checkpoint': osp.abspath(osp.join(tmpDir.root, 'sharedData', 'latest.pth'))
            })

        print(run.run_id)

        # download the output artifact
        client = mlflow.tracking.MlflowClient()
        client.download_artifacts(run.run_id, 'output.json', tmpDir.root)

        if not osp.isfile(output_file):
            raise FileNotFoundError('Could not find "output.json" file. Please log this as an artifact in your code: mlflow.log_artifact(\'output.json\')')

        # collect the results
        with open(output_file, 'r') as output_json:
            return json.load(output_json)

@app.post("/cellpose/")
async def cellpose(file: UploadFile = File(...)):

    # write file to temporary folder
    with TempFolder() as tmpDir:

        # write image file
        input_file = osp.join(tmpDir.root, 'input.png')
        output_file = osp.join(tmpDir.root, 'output.json')

        with open(input_file, 'wb') as output:
            output.write(file.file.read())

        # execute the project
        run = mlflow.projects.run(
            'https://gitlab+deploy-token-1:jzCPzEwRQacvqp8z2an9@jugit.fz-juelich.de/mlflow-executors/cellpose-executor.git',
            entry_point='main',
            version='main',
            backend='local',
            storage_dir=tmpDir.root,
            parameters={
                'input_image': osp.abspath(input_file),
            })

        print(run.run_id)

        # download the output artifact
        client = mlflow.tracking.MlflowClient()
        client.download_artifacts(run.run_id, 'output.json', tmpDir.root)

        if not osp.isfile(output_file):
            raise FileNotFoundError('Could not find "output.json" file. Please log this as an artifact in your code: mlflow.log_artifact(\'output.json\')')

        # collect the results
        with open(output_file, 'r') as output_json:
            return json.load(output_json)

@app.post("/image-prediction/")
async def image_prediction(repo: str, entry_point: Optional[str] = 'main', version: Optional[str] = 'main', file: UploadFile = File(...), parameters: Optional[str] = None):

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
                'input_image': osp.abspath(input_file),
                **additional_parameters
            })

        print(run.run_id)

        # download the output artifact
        client = mlflow.tracking.MlflowClient()
        client.download_artifacts(run.run_id, 'output.json', tmpDir.root)

        if not osp.isfile(output_file):
            raise FileNotFoundError('Could not find "output.json" file. Please log this as an artifact in your code: mlflow.log_artifact(\'output.json\')')

        # collect the results
        with open(output_file, 'r') as output_json:
            result = json.load(output_json)
            result['filename'] = file.filename
            return result

@app.post("/batch-image-prediction/")
async def batch_image_prediction(repo: str, entry_point: Optional[str] = 'main', version: Optional[str] = 'main', files: List[UploadFile] = File(...), parameters: Optional[str] = None):
    """Batch image segmentation for multiple image files

    Args:
        repo (str): git url to the repo containing mlflow project with segmentation
        entry_point (Optional[str], optional): mlproject entry point. Defaults to 'main'.
        version (Optional[str], optional): Commit hash/branch/tag of the git repo. Defaults to 'main'.
        files (List[UploadFile], optional): List of image files. Defaults to File(...).
        parameters (Optional[str], optional): Additional parameters to pass on to the repo segmentation approach. Defaults to None.

    Returns:
        [List]: python list of segmentation results for every image
    """
    results = []

    # loop over files
    for file in files:
        # perform image prediction for every file
        json_result = await image_prediction(repo, entry_point, version, file, parameters)
        results.append(json_result)
    return results


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app",host='0.0.0.0', port=4557, reload=True, debug=True, workers=3)