FROM alpine:3.13

RUN apk update && apk add --no-cache python3-dev py3-pip gcc musl-dev

RUN mkdir /fossnewsbot
WORKDIR /fossnewsbot

COPY requirements.txt .
COPY main.py .
COPY fngsapi.py .
COPY config.json .

RUN pip3 install -r requirements.txt
CMD python3 main.py