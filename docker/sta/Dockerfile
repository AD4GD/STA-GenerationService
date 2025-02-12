ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG user_path="/home/sta_user"
RUN useradd --create-home -s /bin/bash sta_user

COPY reqs/sta.txt $user_path/requirements.txt
RUN pip install --no-cache-dir --upgrade -r $user_path/requirements.txt

COPY src/sta $user_path
COPY docker/sta/scripts $user_path/scripts
COPY docker/sta/resources $user_path/resources
COPY docker/sta/alembic/alembic.ini $user_path
COPY docker/sta/alembic/script.py.mako $user_path/alembic

RUN chown -R sta_user:sta_user $user_path

USER sta_user
WORKDIR $user_path

CMD ["./scripts/server.sh"]
