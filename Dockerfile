FROM python:3.9-slim-buster

WORKDIR '/app'
COPY . .
RUN pip install -r requirements.txt
ENTRYPOINT ["python3", "main.py"]