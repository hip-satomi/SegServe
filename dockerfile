FROM pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime

RUN apt-get update && apt-get install -y python3-opencv

RUN mkdir app/

RUN mkdir /home/appuser/

RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser

RUN chown -R appuser:appuser app/
RUN chown -R appuser:appuser /home/appuser/

RUN chown -R appuser:appuser /opt/conda

WORKDIR /home/appuser/

USER appuser



RUN conda install mamba -c conda-forge -y


COPY ./requirements.txt ./

RUN conda create -y -n serve python=3.8.5 mamba git -c conda-forge

RUN conda run -n serve \
  python -m pip install -r requirements.txt

RUN conda run -n serve python --version

# Make RUN commands use the new environment:
SHELL ["/bin/bash", "--login", "-c"]
RUN conda init bash
RUN echo "conda activate serve" >> /home/appuser/.bashrc

COPY ./entrypoint.sh ./

ENV MLFLOW_CONDA_CREATE_ENV_CMD=mamba
ENV CACHE_FOLDER="/home/appuser/cache"
RUN mkdir -p ${CACHE_FOLDER}

# pre-install segmentation approaches (faster execution later on)

## cellpose/omnipose
RUN conda run -n serve mlflow run https://gitlab+deploy-token-1:jzCPzEwRQacvqp8z2an9@jugit.fz-juelich.de/mlflow-executors/cellpose-executor.git -e info -v main
## mmdetection
RUN conda run -n serve mlflow run https://gitlab+deploy-token-1:jzCPzEwRQacvqp8z2an9@jugit.fz-juelich.de/mlflow-executors/mmdetection-executor.git -e info -v main
## yolov5
RUN conda run -n serve mlflow run https://gitlab+deploy-token-1:jzCPzEwRQacvqp8z2an9@jugit.fz-juelich.de/mlflow-executors/yolov5-executor.git -e info -v master

ENTRYPOINT ["./entrypoint.sh"]

COPY ./sharedData ./sharedData
COPY ./main.py ./
COPY ./utils.py ./

EXPOSE 8000
#CMD [ \
  #"conda activate serve" \
  #"conda", "activate", "serve", "&&" \
  #"conda", "run", "-n", "serve", \
  #"uvicorn", "main:app" \
#]
