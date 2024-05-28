FROM python:3.10-bullseye

ENV APP_HOME=/home/app/web
WORKDIR $APP_HOME

COPY ./requirements.txt .
RUN  pip install --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=billing_db models.py db/models.py
RUN addgroup --system api_group &&  \
    adduser --system --ingroup api_group api_user &&  \
    chown --recursive api_user:api_group $APP_HOME

EXPOSE 8000
USER api_user
ENTRYPOINT [ "gunicorn",  "main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", \
             "--bind", "0.0.0.0:8000" ]
