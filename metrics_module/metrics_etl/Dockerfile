FROM python:3.10-bullseye

ENV APP_HOME=/home/app/web
WORKDIR $APP_HOME

COPY ./requirements.txt .
RUN  pip install --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN addgroup --system api_group &&  \
    adduser --system --ingroup api_group api_user &&  \
    chown --recursive api_user:api_group $APP_HOME

EXPOSE 8000
USER api_user
ENTRYPOINT [ "python3",  "main.py" ]
