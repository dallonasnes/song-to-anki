FROM python:latest
RUN apt-get update

ENV APP_HOME /usr/src/app
WORKDIR /$APP_HOME

COPY ./ $APP_HOME/
RUN pip install --no-cache-dir -r requirements.txt
#RUN python -m nltk.downloader all

ENV FLASK_ENV="docker"
EXPOSE 5000
