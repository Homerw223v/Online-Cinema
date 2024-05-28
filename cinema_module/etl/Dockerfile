FROM python:3.10-bullseye

ENV APP_HOME=/home/app/etl
WORKDIR $APP_HOME

RUN addgroup --system etl &&  \
    adduser --system --ingroup etl etl &&  \
    chown --recursive etl:etl $APP_HOME

COPY ./requirements.txt .
RUN  pip install --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt

COPY . $APP_HOME

USER etl
ENTRYPOINT [ "python3", "main.py" ]
