FROM python:3.8.1

RUN apt-get update && apt-get install -y youtube-dl

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY . /app
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
