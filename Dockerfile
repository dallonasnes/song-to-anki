# pull official base image
FROM python:3.8

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gcc python3-dev
#&& apk add postgresql-dev gcc python3-dev musl-dev

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN export LDFLAGS="-L/usr/local/opt/openssl/lib"
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/

EXPOSE 5000

RUN ls -la /usr/src/app/
RUN chmod +x /usr/src/app/docker-entrypoint.sh

ENTRYPOINT ["/usr/src/app/docker-entrypoint.sh"]
