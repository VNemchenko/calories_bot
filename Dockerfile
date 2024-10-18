FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt requirements.txt
COPY ./packages /packages
RUN pip install --find-links=/packages -r requirements.txt

COPY app .

CMD ["python", "/app/run_new.py"]
