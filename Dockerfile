ARG USER=serverurser
ARG WORKDIR=/home/$USER/server

# Python STAGE 1
FROM python:3.12 AS builder

ARG USER
ARG WORKDIR

WORKDIR $WORKDIR

RUN mkdir -p $WORKDIR

# Setup the required packages
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Python STAGE 2
FROM python:3.12-slim

ARG USER
ARG WORKDIR

# copy the installed Python modules
COPY --from=builder /install /usr/local

RUN mkdir -p $WORKDIR
WORKDIR $WORKDIR

# install the own modules
COPY main.py .
COPY MyServer $WORKDIR/MyServer
COPY start.sh .
RUN chmod +x start.sh

# do NOT run as root
RUN useradd -m -d /home/$USER $USER
RUN chown -R $USER:$USER $WORKDIR
USER $USER

ENV LOGGING_LEVEL=INFO

# Ports to expose, we are using a OPC UA server here
EXPOSE 4840 8765

CMD ["./start.sh"]
