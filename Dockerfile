FROM ubuntu:jammy

ARG PWD=postgres

# install postgres 17
RUN apt-get update
RUN apt-get install -y lsb-release curl gnupg2 wget ca-certificates make
RUN bash -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install postgresql-17 postgresql-client-17 -y
RUN /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y

# install postgis
RUN apt install -y postgresql-17 postgresql-17-postgis-3 postgis

# install timescaledb
RUN apt install gnupg postgresql-common apt-transport-https lsb-release wget -y
RUN echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" | tee /etc/apt/sources.list.d/timescaledb.list
RUN wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | gpg --dearmor -o /etc/apt/trusted.gpg.d/timescaledb.gpg
RUN apt update
RUN apt install timescaledb-2-postgresql-17 postgresql-client-17 -y
RUN timescaledb-tune --quiet --yes -pg-version 17

RUN apt install systemd -y
RUN systemctl enable postgresql
RUN service postgresql restart

# change postgres password
RUN  su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD '${PWD}';\""
# create user cellsight
RUN  su - postgres -c "psql -c \"CREATE USER cellsight WITH PASSWORD '${PWD}}';\""


# set working directory
WORKDIR /usr/local/cellsight
COPY ./src /usr/local/cellsight/src
COPY ./config /usr/local/cellsight/config
COPY ./.env /usr/local/cellsight/.env
COPY ./environment.yml /usr/local/cellsight/environment.yml
COPY ./Makefile /usr/local/cellsight/Makefile

# install conda
RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O Miniforge3-Linux-x86_64.sh
RUN bash Miniforge3-Linux-x86_64.sh -b -p /opt/conda
ENV PATH="/opt/conda/bin:$PATH"

# create conda environment
RUN conda env create -n cellsight -f environment.yml