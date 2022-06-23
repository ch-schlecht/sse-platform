FROM python:3.10-slim-buster

WORKDIR /sse-platform

COPY . .

# need wget to perform the healthcheck
RUN apt update
RUN apt install wget -y

RUN pip3 install -r requirements.txt

EXPOSE 8888

CMD [ "python3", "-u", "main.py" ]