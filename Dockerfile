FROM alpine:3.10

ARG build_version
ENV BUILD_VERSION=${build_version}

ARG develop
ENV DEVELOP=${develop}

ENV USER=app-user
ENV UID=900
ENV GID=901

RUN addgroup --gid "$GID" "$USER" && adduser -D -H -u "$UID" "$USER" -G "$USER"

# hadolint ignore=DL3013,DL3018
RUN apk add --update --no-cache --virtual .build-tmp build-base postgresql-dev && \
    apk add --update --no-cache make python3-dev py3-psycopg2 && \
    pip3 install --upgrade pip

WORKDIR /service
RUN chown -R "$USER":"$USER" /service

COPY ./requirements /service/requirements
COPY ./requirements.txt /service/requirements.txt

RUN pip3 install -r requirements.txt && \
    if [ $DEVELOP ]; then \
        pip3 install -r /service/requirements/development.txt; \
    fi

RUN apk --purge del .build-tmp

COPY . /service

# pylint staff
RUN mkdir -p /home/app-user/ && chown -R "$USER":"$USER" /home/app-user/

USER "$USER"
CMD ["/bin/sh"]
