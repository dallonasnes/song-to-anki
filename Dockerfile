FROM ubuntu:bionic
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libnspr4 libnss3 lsb-release xdg-utils libgbm1 libxss1 libdbus-glib-1-2 \
    apt-utils curl unzip wget vim\
    xvfb

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONUNBUFFERED=1

ENV APP_HOME /usr/src/app
WORKDIR /$APP_HOME

COPY ./ $APP_HOME/
COPY ./requirements.txt $APP_HOME/
RUN pip3 install -r requirements.txt
RUN python3 -m nltk.downloader all

# add and run as non-root user
RUN adduser myuser
USER myuser

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]