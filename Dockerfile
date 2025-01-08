FROM python:3.12

COPY . /contrainer
WORKDIR /contrainer
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "watcher.py"]
CMD ["python3", "watcher.py"]