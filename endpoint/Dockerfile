FROM alpine:latest

COPY . /api

WORKDIR /api

RUN apk update && apk add python3 && apk add py3-pip && pip3 install -r requirements.txt

EXPOSE 5000

CMD ["python3", "main.py"]
