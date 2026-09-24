# Gracefully handle daemon termination
import os
import uvicorn
import logging
import pathlib
from typing import Any

from scape.server.main import app
from scape.daemon.control.sock import create_tcp_sock, create_file_sock

logger = logging.getLogger(__name__)

class Daemon:
    def __init__(self, socket_host: str | None = None, socket_port: int | None = None, socket_file: str | None = None) -> None:
        self.socket_host : str | None = socket_host
        self.socket_port : int | None = socket_port
        self.socket_file : str = socket_file if socket_file else os.environ.get('XDG_RUNTIME_DIR', f"/tmp") + "/scape.sock"


    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass

    def loop(self, ) -> None:
        if self.socket_host and self.socket_port:
            logger.info(f"Creating TCP socket for {self.socket_host}:{self.socket_port}")
            uvicorn.run(app=app, host=self.socket_host, port=self.socket_port)
        else:
            logger.info(f"Creating File socket at {self.socket_file}")
            uvicorn.run(app=app, uds=self.socket_file)
        