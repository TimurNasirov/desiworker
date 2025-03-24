FROM python:3.12

COPY . /rentacar
WORKDIR /rentacar
RUN pip3 install -r requirements.txt

CMD ["python3", "watcher.py", "--read-only"]