FROM python:3.9.4

RUN pip install --upgrade pip \
    && mkdir /app

ADD . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD python /app/tech_bot.py
