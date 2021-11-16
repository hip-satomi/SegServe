# Serve Segmentation Server

This project provides an http server that automatically launches segmentation approaches based on mlflow-configured git repositories. The http server is deployed in a docker container featuring:

- nvidia gpu support
- conda/mamba
- base configuration in "serve" environment

You can easily launch the server using
```
uvicorn --host 0.0.0.0 main:app
```

This launches the segmentation server at port 8000.

`Hint:` For using the GPU inside the container you usually have to launch it using

```
docker run ... --gpus all ...
```

or use the `runtime: nvidia` option in docker-compose (use a recent version).

`Hint:` You need to expose the port for accessing it from your local computer, e.g.

```
docker run ... -p 8000:8000 ...
```

connects the port `8000` of your computer to port `8000` in the container.

# API documentation

The server comes with an api documentation that is accessible under `/docs`. It also provides an interactive user interface to test approaches.
