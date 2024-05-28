###########
# BUILDER #
###########

FROM python:3.10-bullseye as builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y gcc python3-dev musl-dev libpq5 gettext

COPY ./requirements.txt .

RUN pip cache purge && \
    pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# FINAL #
#########

FROM python:3.10-bullseye as prod

ENV APP_HOME=/home/app/web
RUN mkdir -p $APP_HOME && mkdir $APP_HOME/staticfiles && mkdir $APP_HOME/mediafiles && \
    apt-get update && \
    apt-get install -y gettext
WORKDIR $APP_HOME

COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

COPY . $APP_HOME

RUN addgroup --system app_group &&  \
    adduser --system --ingroup app_group app &&  \
    chown --recursive app:app_group $APP_HOME && \
    chmod +x $APP_HOME/docker-entrypoint.sh

USER app
