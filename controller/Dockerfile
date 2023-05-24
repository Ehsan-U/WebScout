FROM alpine:latest

COPY . .

RUN apk update && apk add python3 && apk add py3-pip && pip3 install pymongo

CMD ["python3", "monitor.py"]