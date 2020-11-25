FROM python:3.8.1

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY . /app
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
