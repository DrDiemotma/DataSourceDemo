# Data Source Demo Version 0.0.1
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
In contrast to REST, the client creates a session on server side in order to be able to receive the data.
The data itself is created on server side.

![Network connection](Images/[OAB]%20Activities%20for%20Data%20Receiving.png)

In principle, control of the server can be implemented by implementing functions in the OPC UA interface.
In this simulated server, the OPC UA side is considered alike a real machine:
controls are implemented in different means.
In a physical machine, this is controlled for example by physical limitations, that is, a sensor is exposed if the sensor is physically present and the data is meant to be presented.
In this simulation, this configuration is performed through a REST API.

![API and simulation setup](Images/[OAB]%20OpcUaServer.png)

The API is currently under development in this early stage.
Once it is mature enough, it will receive version 0.1.
Currently, it is moving fast, therefore handle with care.
You can find the current API in `MyServer/Api/api_router.py`.

### Sensor Management
The core of this software is the sensor management component.
Here, sensors are set up and data is generated.
Notice that this so far is a simulation, meaning that the driver takes in the role of creating random signals.
There is no hardware connection with the driver.
These values are written to the sensor representation.
This again is very similar to real sensors.
The data is then written in the data model.

![Simulated sensors and drivers](Images/[OAB]%20Machine%20Model.png)

Because of technical limitations of the asyncua server implementation, there is no update modus implemented yet.
Hence, a client must implement a polling mechanism.