FROM python:3.12

COPY . /rentacar
WORKDIR /rentacar
RUN pip3 install -r requirements.txt
RUN ["mkdir", "/rentacar/logs"]
RUN ["mkdir", "/rentacar/exword_results"]

CMD ["python3", "main.py"]