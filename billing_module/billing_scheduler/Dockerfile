FROM python:3.10-bullseye

ENV APP_HOME=/home/app/web
WORKDIR $APP_HOME

COPY ./requirements.txt .
RUN  pip install --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=billing_db models.py database/models.py
RUN addgroup --system scheduler_group &&  \
    adduser --system --ingroup scheduler_group scheduler_user &&  \
    chown --recursive scheduler_user:scheduler_group $APP_HOME

EXPOSE 8000
USER scheduler_user
ENTRYPOINT [ "python",  "main.py" ]
