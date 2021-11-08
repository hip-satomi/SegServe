FROM continuumio/miniconda3:4.10.3

RUN mkdir app/

WORKDIR app/

RUN conda install mamba -c conda-forge -y


COPY ./requirements.txt ./
COPY ./sharedData ./sharedData
COPY ./main.py ./
COPY ./utils.py ./

RUN conda create -n serve python=3.8.5

RUN conda run -n serve \
  python -m pip install -r requirements.txt

RUN conda run -n serve python --version

# Make RUN commands use the new environment:
RUN echo "conda activate serve" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

COPY ./entrypoint.sh ./

ENTRYPOINT ["./entrypoint.sh"]

#CMD [ \
#  "conda activate serve" \
  #"conda", "activate", "serve", "&&" \
  #"conda", "run", "-n", "serve", \
  #"uvicorn", "main:app" \
#]
