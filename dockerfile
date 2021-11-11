FROM python:3.8
RUN apt-get -y update
RUN apt-get -y install libgdal-dev gdal-bin

COPY data/ /data
COPY main.py .

ENTRYPOINT python main.py