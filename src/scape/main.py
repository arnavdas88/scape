import os
import time
import asyncio
import logging

from scape.daemon import Daemon

logging.basicConfig(level=logging.DEBUG, filename=f"/var/log/{__name__}.log")

def main():
    logger = logging.getLogger(__name__)
    logger.info("Daemon has started up successfully.")
    
    daemon = Daemon(socket_host="0.0.0.0", socket_port=8000)
    daemon.loop()
        
    logger.info("Daemon received exit signal. Cleaning up and shutting down.")


if __name__ == "__main__":
    main()