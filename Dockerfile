
FROM python:3.9-alpine


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


WORKDIR /app


RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libffi-dev openssl-dev

COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

RUN apk del .build-deps

COPY ./app .

CMD ["python", "app/main.py"]


