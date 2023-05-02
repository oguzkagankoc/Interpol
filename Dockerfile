FROM ubuntu:jammy

ENV TZ=Europe/Istanbul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && \
    apt-get -y install gnupg2 curl lsb-release python3-dev && \
    echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list && \
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get -y install postgresql python3-pip libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install sqlalchemy psycopg2

RUN service postgresql start && \
    su - postgres -c "psql -c \"ALTER USER postgres PASSWORD '122333';\"" && \
    su - postgres -c "createdb task2" ## && \
    #service postgresql stop

EXPOSE 5432

WORKDIR /app
COPY database_creation.py .

CMD service postgresql start && \
    python3 database_creation.py ## && \
    #service postgresql stop
