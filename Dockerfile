# Use an official Python runtime as a parent image
#FROM python:3.9
FROM python:alpine
#FROM ubuntu:latest

# Set the working directory in the container to /app
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "run.py"]




