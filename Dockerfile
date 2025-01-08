FROM python:3.12

COPY . /contrainer
WORKDIR /contrainer

CMD ["python3", "watcher.py"]