FROM continuumio/miniconda3:4.10.3

RUN mkdir app/

RUN mkdir /home/appuser/

RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser appuser

RUN chown -R appuser:appuser app/
RUN chown -R appuser:appuser /home/appuser/

RUN chown -R appuser:appuser /opt/conda

WORKDIR app/

USER appuser



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
