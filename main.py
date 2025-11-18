import sys

from MyServer import opc_ua_server
from fastapi import FastAPI
from fastapi.responses import FileResponse
from MyServer.Api import router_v01, router_examples
from MyServer.Lifetime import MachineModel
import logging
from logging.handlers import RotatingFileHandler
import uvicorn
import argparse

app = FastAPI(title="OPC UA Server Demo")
machine_model: MachineModel = MachineModel()
server = opc_ua_server.OpcUaTestServer(machine=machine_model)
app.state.server = server
app.include_router(router_v01, prefix="/v0.1")
app.include_router(router_examples, prefix="/v0.1")

def start_service(level, port: int = 8765):
    handler = RotatingFileHandler(
        "DataSourceDemo.log",
        maxBytes=10_485_760,  # 10 MB,
        backupCount=10
    )

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    root_logger.addHandler(stream_handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)

    logging.info(f"Starting FastAPI service on port {port}.")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, log_config=None)

@app.get("/", response_class=FileResponse)
async def root():
    return "static/index.html"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--logging-level",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    args = parser.parse_args()
    log_level = getattr(logging, args.logging_level.upper(), logging.INFO)

    start_service(log_level)
