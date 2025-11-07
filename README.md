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
