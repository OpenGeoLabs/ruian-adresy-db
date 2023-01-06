FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update &&  \
    apt-get install -y libgdal28 libgdal-dev binutils gdal-bin gdal-data

RUN python3 -m pip install --no-cache-dir -r requirements.txt