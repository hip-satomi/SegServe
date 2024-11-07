FROM mambaorg/micromamba:1.5.5-focal-cuda-11.6.2

ARG NEW_MAMBA_USER=mambauser
ARG NEW_MAMBA_USER_ID=1000
ARG NEW_MAMBA_USER_GID=1000

#RUN apt-get update && apt-get install -y python3-opencv
ARG MAMBA_DOCKERFILE_ACTIVATE=1

WORKDIR /home/$MAMBA_USER

COPY ./requirements.txt ./

RUN micromamba install -y python=3.8 mamba git -c conda-forge

RUN python -m pip install -r requirements.txt

RUN python --version

COPY ./entrypoint.sh ./

ENV MLFLOW_CONDA_CREATE_ENV_CMD=/opt/conda/bin/mamba
ENV MLFLOW_CONDA_HOME=/opt/conda
ENV CACHE_FOLDER="/home/$MAMBA_USER/cache"
RUN mkdir -p ${CACHE_FOLDER}

# pre-install segmentation approaches (faster execution later on)

RUN ln -s /opt/conda/bin/mamba /opt/conda/bin/conda

## cellpose/omnipose
RUN mlflow run https://github.com/hip-satomi/Cellpose-Executor.git -e info -v main
## mmdetection
RUN mlflow run https://github.com/hip-satomi/MMDetection-Executor.git -e info -v main
## yolov5
RUN mlflow run https://github.com/hip-satomi/Yolov5-Executor.git -e info -v main
## Omnipose
RUN mlflow run https://gitlab+deploy-token-281:TZYmjRQZzLZsBfWsd2XS@jugit.fz-juelich.de/mlflow-executors/omnipose-executor -e info -v main

# copy scripts
COPY ./main.py ./
COPY ./utils.py ./
COPY ./influx.py ./

EXPOSE 8000

CMD ["uvicorn", "--host", "0.0.0.0", "main:app"]
#CMD [ \
  #"conda activate serve" \
  #"conda", "activate", "serve", "&&" \
  #"conda", "run", "-n", "serve", \
  #"uvicorn", "main:app" \
#]
