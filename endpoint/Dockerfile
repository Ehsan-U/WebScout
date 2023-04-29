FROM alpine:latest

COPY . /api

WORKDIR /api

RUN apk update && apk add python3 && apk add py3-pip && pip3 install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
