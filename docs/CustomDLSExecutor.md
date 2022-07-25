# Designing your custom DLS executor

A customized deep-learning segmentation (DLS) model or nouveau approach that is not yet implement for `SegServe` require a custom executor implementation.

The implementation is always performed in form of a git repository that is publicly available via a url. This repository has to follow a specific but simple format to be executed seamlessly by `SegServe`.

## Repository structure

The repository must fullfill two requirements:

1. Outline software dependencies and entrypoints in [mlproject](https://www.mlflow.org/docs/latest/projects.html)
2. Output segmentation results in json format readable by `SegServe`



### 1. Dependency management
The software dependencies and entrypoints are managed using [mlproject](https://www.mlflow.org/docs/latest/projects.html). This is performed in a declarative `MLProject` file at the root of your project.

```
Your repository
| ...
|- MLProject
| ...
```

This `MLProject` file allows to specify the runtime dependencies in form of `conda` yaml files or docker containers. Furthermore, it defines the exposed entrypoints and their corresponding parameters. An examplary `MLProject` file from the [Cellpose-Executor](https://github.com/hip-satomi/Cellpose-Executor) looks like this:

```
name: CellPose-Executor Project

conda_env: conda.yaml

entry_points:
  main:
    parameters:
      input_images: path
    command: "python main.py {input_images}"

  omnipose:
    parameters:
      input_images: path
    command: "python main.py --omni {input_images}"

  info:
    command: "python info.py"
```

It specifies `conda_env`, a file contained in your repository with a conda environment definition, and lists multiple entrypoints. The entrypoints can provide various functionality:

 - The `main` entrypoint gets an `input_images` parameter (path to a directory containing images) that is passed on to a python script execution that executes the [Cellpose](https://www.nature.com/articles/s41592-020-01018-x) on all images.
 - The `omnipose` entrypoint has the same parameters but calls the underlying script with a specific flag to execute the [Omnipose](https://arxiv.org/abs/2103.10180) method on all images.
 - The `info` entrypoint does not perform any segmentation.

 Therefore, a single git repository can deal as an executor for different segmentation methods as long as you specify separate entrypoints for them.

 ### 2. Segmentation data format

 To provide the segmentation to the end-user the executed segmentation method (e.g. python script) must save the results in the `output.json` file and register the output with `mlflow`
 ```python
 mlflow.log_artifact('output.json')
 ```

The `output.json` file contains a header giving information about the executing model and format version and an array of segmentations. To support batch processing this is always an array for multiple images.

Here is an example of a possible segmentation output
```
{
    "model": "https://github.com/hip-satomi/Cellpose-Executor.git#dcded8b",
    "format_version": "0.2",
    "segmentation_data": [
        [
            {
                "label": "Cell",
                "contour_coordinates": [
                    [
                        932,  # <-- x
                        267   # <-- y
                    ],
                    [
                        931,
                        268
                    ],
                    .
                    . more coordinates
                    .
                ],
                "type": "Polygon"
            },
            .
            . multiple objects in the image
            .
        ],
        .
        . multiple images (e.g. batch prediction)
        .
    ]
}

```

## Usage

When these two requirements are fulfilled, your segmentation can be used with `SegServe` or immediately in `SegUI`.