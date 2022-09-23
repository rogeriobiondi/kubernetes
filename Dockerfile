FROM python:3.10.4-slim

RUN apt-get clean \
    && apt-get -y update

RUN apt-get -y install \
    nginx \
    python3-dev \
    build-essential

WORKDIR /app
COPY microsvc /app/microsvc
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt --src /usr/local/src

COPY . .

EXPOSE 8000

CMD [ "uvicorn", "microsvc.main:app", "--host", "0.0.0.0" ]