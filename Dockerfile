FROM python:alpine

WORKDIR /app

COPY requirements.txt requirements.txt
COPY ./packages /packages
RUN pip install --find-links=/packages -r requirements.txt

COPY . .

CMD ["python", "run_new.py"]
