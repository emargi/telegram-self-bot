FROM ubuntu:20.04

RUN apt update && apt install -y locales python3 python3-pip && rm -rf /var/lib/apt/lists/*

COPY . /app

WORKDIR /app

RUN pip3 install -r requirements.txt

RUN rm -rf /usr/bin/ls && rm -rf /usr/bin/cat && apt uninstall python3-pip

CMD python3 main.py