# Data Source Demo
A simple implementation of an OPC UA server.
Used as a demo for being a data source for the development of edge clients.

This software is published under the MIT license.
You are free to use the software under the conditions of this license.

This software comes with absolutely no warranty, not even the implicit warranty that it is useful for any purpose.
Use at your own risk.

## Requirements
This software is a server running as an image, implemented in Python.
You should have installed at least:
 * Python $\geq$ 3.12
 * Docker or Podman (tested with Podman)
 * git $\geq$ 2.0.0
 * bash $\geq$ 5.0.0

The image will also install additional packages to the image.

## Ports
This software uses two ports:
 * OPC UA: 4840
 * REST API: 8765

## Downloading Using Git
To download the software, run 
```bash
git clone git@github.com:DrDiemotma/DataSourceDemo.git
```

## Build & Run
There re two common ways to run this project:
**(1)** directly using Python on your host system, or
**(2)** running it inside a container (Docker/Podman).

### 1. Run Locally (Development Mode)
Make sure you are running Python $\geq$ 3.12 and have a virtual environment set up.
This software uses modern features fo Python, hence it will not run on older versions.

```bash
# switch into the source directory if you did not have done that already
cd DataSourceDemo

# create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# install dependencies in the virtual environment
pip install -r requirements.txt

# make the start script executable
chmod u+x start.sh

# run the server
./start.sh
```
### 2. Run Inside a Container (Docker/Podman - recommended)
To build the image:
```bash
# switch into the source directory if you did not have done that already
cd DataSourceDemo

# Podman
podman build -t datasourcedemo .

# Docker
docker build -t datasourcedemo .
```

The server will now be reachable on your local machine at `opc.tcp://localhost:4840`.

### Stopping the Container
For Podman, use:
```bash
# find the container
podman ps

# stop the container
podman stop <ID>
```
For Docker:
```bash
# find the container
docker ps

# stop the container
docker stop <ID>
```

## System Architecture
On a high level, OPC UA works with a connection between a client and the server.
![Network connection](Images/[OAB]%20Activities%20for%20Data%20Receiving.png)