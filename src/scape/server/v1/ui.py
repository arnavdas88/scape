import io
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from pydantic import BaseModel
from fastapi import FastAPI, APIRouter, HTTPException, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from paramiko import Ed25519Key, RSAKey, ECDSAKey

from scape.server.models import SSHSession, SSHHost, SSHCredential
from scape.server.managers import CredentialStore, HostStore, SSHSessionManager
from scape.server.base import hosts, credentials, sessions

BASE_DIR = Path(__file__).resolve().parent

ui_sub_router = APIRouter(prefix="/v1/ui", tags=["UI"])

ui_sub_router.mount( "/static", StaticFiles( directory=BASE_DIR / "static", html=True, ), name="static", )

@ui_sub_router.websocket("/sessions/{session_id}/terminal")
async def terminal( websocket: WebSocket, session_id: str, ):
    await websocket.accept()

    try:
        session = sessions.get(session_id)
    except KeyError:
        await websocket.close(code=4404)
        return

    channel = session.channel

    async def ssh_to_ws():
        while not channel.closed:

            if channel.recv_ready():
                data = channel.recv(65536)

                if not data:
                    break

                session.touch()
                await websocket.send_bytes(data)

            elif channel.recv_stderr_ready():
                data = channel.recv_stderr(65536)

                if data:
                    await websocket.send_bytes(data)

            else:
                await asyncio.sleep(0.01)

    async def ws_to_ssh():
        while not channel.closed:

            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if "bytes" in message and message["bytes"] is not None:
                channel.send(message["bytes"])
                session.touch()

            elif "text" in message and message["text"] is not None:
                channel.send(message["text"])
                session.touch()

    try:
        await asyncio.gather( ssh_to_ws(), ws_to_ssh(), )
    finally:
        sessions.close(session_id)

@ui_sub_router.get("/terminal/{session_id}")
async def terminal_page(session_id: str):

    try:
        sessions.get(session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    return FileResponse(
        BASE_DIR / "static" / "terminal.html"
    )