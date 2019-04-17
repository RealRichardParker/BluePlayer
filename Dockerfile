FROM ubuntu:18.04
RUN apt-get update -y \ 
    && apt-get install -y python-setuptools python-pip
RUN pip install virtualenv --upgrade
ADD requirements.txt /src/requirements.txt
RUN cd /src; pip install -r requirements.txt
ADD . /src
EXPOSE 5000
CMD ["python", "/src/music_app.py"]

