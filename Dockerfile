FROM python:3.11

WORKDIR /code

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

COPY requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/

RUN mkdir -p /code/logs

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]