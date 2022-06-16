FROM python:3.10-slim-buster

WORKDIR /sse-platform

COPY . .

RUN pip3 install -r requirements.txt

EXPOSE 8888

CMD [ "python3", "-u", "main.py" ]