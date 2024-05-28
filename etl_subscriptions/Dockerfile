###########
# BUILDER #
###########

FROM python:3.10-bullseye as builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y libpq-dev

COPY ./requirements.txt .

RUN pip cache purge && \
    pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# FINAL #
#########

FROM python:3.10-bullseye as prod

ENV APP_HOME=/home/app/initializer
WORKDIR $APP_HOME
RUN addgroup --system initializer &&  \
    adduser --system --ingroup initializer initializer &&  \
    chown --recursive initializer:initializer $APP_HOME

RUN apt-get update && \
    apt-get install -y postgresql
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

COPY . .

USER initializer
ENTRYPOINT [ "/bin/bash", "entripoint.sh" ]