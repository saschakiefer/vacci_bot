FROM python:slim

RUN apt-get update
RUN apt-get install -y locales locales-all
COPY bot/* /bot/
COPY requirements.txt /tmp
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install -r /tmp/requirements.txt

WORKDIR .
CMD ["python3", "./bot/main.py"]
