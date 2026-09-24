import io
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from paramiko import Ed25519Key, RSAKey, ECDSAKey

from scape.server.models import SSHSession, SSHHost, SSHCredential
from scape.server.managers import CredentialStore, HostStore, SSHSessionManager
from scape.server.base import hosts, credentials, sessions

from scape.server.v1.management import management_sub_router as management_sub_router
from scape.server.v1.ui import ui_sub_router as ui_sub_router

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup

    yield

    # Shutdown

    # Clean up any and all active sessions
    for session_id in list(sessions.sessions):
        sessions.close(session_id)

app = FastAPI(lifespan=lifespan)
app.include_router(management_sub_router)
app.include_router(ui_sub_router)

@app.get("/")
def index():
    return {"status": "ok"}