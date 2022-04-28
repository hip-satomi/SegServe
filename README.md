# Segmentation Server

This project provides a REST API for DL segmentation methods that automatically manages installtion on-demand based on mlflow-configured git repositories. The REST API is deployed in a docker container featuring:

- nvidia gpu support
- conda/mamba
- base configuration in "serve" environment

# Setup

You can easily launch the server locally using
```
docker build -t segserve .
docker run -it -p 8000:8000 segserve
```

This launches the segmentation server at port 8000.

`Hint:` For using the GPU inside the container you usually have to launch it using

```
docker build -t segserve .
docker run -it -p 8000:8000 --gpus all segserve
```

or use the `runtime: nvidia` option in `docker-compose` (use a recent `docker-compose` version).

`Hint:` You need to expose the port for accessing it from your local computer, e.g.

```
docker run ... -p 8000:8000 ...
```

connects the port `8000` of your computer to port `8000` in the container.

# Usage

To use `SegServe` for segmentation you can access the REST API, for example, using `curl`. Here is a bash example that first downloads an example image and then requests the segmentation from `SegServe` using the [Omnipose] segmentation method:

```bash
wget https://fz-juelich.sciebo.de/s/wAXbC0MoN1G3ST7/download -O localhost.jpeg
curl -X 'POST' \
  'http://localhost:8001/batch-image-prediction/?repo=https%3A%2F%2Fgithub.com%2Fhip-satomi%2FCellpose-Executor.git&entry_point=omnipose&version=main' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@localhost.jpeg;type=image/jpeg'
```

# API documentation

The server comes with an api documentation that is accessible at `localhost:8000/docs`. It also provides an interactive user interface to execute various segmentation approaches with different parameters and image files.

# Running behind a proxy

For correctly running behind a proxy you need to a the `--root-path` command to your uvicorn launch specifying the sub-url location where your seg-serve instance is listening. For example

```
docker run ... uvicorn uvicorn --host 0.0.0.0 --root-path=/this/is/your/sub-url/ main:app
```

If you do not configure this, the endpoints will still be accessible but `docs` interactive usage will not work.

# Security

Please note that this REST API allows to execute arbitrary git repositories. Therefore, usage is only recommended with trusted users!

# Debugging

For debugging we recommend to run `SegServe` directly with uvicorn:

```
uvicorn --host 0.0.0.0 main:app
```