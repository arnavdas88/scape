import io
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from paramiko import Ed25519Key, RSAKey, ECDSAKey

from .models import SSHSession, SSHHost, SSHCredential
from .managers import CredentialStore, HostStore, SSHSessionManager

BASE_DIR = Path(__file__).resolve().parent

hosts = HostStore()
credentials = CredentialStore()
sessions = SSHSessionManager(credentials, hosts)

class CreateSessionRequest(BaseModel):
    path: list[str]
    term: str = "xterm"
    width: int = 120
    height: int = 40

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Populate these from your secure configuration/secret store.
    # This will have to be dynamic, through API
    rsa_key_obj = RSAKey.from_private_key(
        io.StringIO(
            open("private.key", "r").read()
        )
    )
    credentials.add( "IdentityFile<Server A>",  SSHCredential(username="user_a", pkey=rsa_key_obj) )
    credentials.add( "Password<Server B>",      SSHCredential(username="user_b", password="SomePassword") )
    credentials.add( "Password<Server C>",      SSHCredential(username="user_c", password="AnotherPassword") )

    hosts.add( SSHHost( name="Server A", hostname="xxx.xxx.xxx.xxx", credential="IdentityFile<Server A>", ) )
    hosts.add( SSHHost( name="Server B", hostname="yyy.yyy.yyy.yyy", credential="Password<Server B>", ) )
    hosts.add( SSHHost( name="Server C", hostname="zzz.zzz.zzz.zzz", credential="Password<Server C>", ) )

    yield

    # Clean up any and all active sessions
    for session_id in list(sessions.sessions):
        sessions.close(session_id)

app = FastAPI(lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "static",
        html=True,
    ),
    name="static",
)

@app.post("/sessions")
async def create_session(req: CreateSessionRequest):
    try:
        session = await asyncio.to_thread(
            sessions.create_session,
            req.path, req.term, 
            req.width, req.height,
        )

    except Exception as exc:
        raise HTTPException( status_code=400, detail=str(exc), )

    return { "session_id": session.id, "path": session.hosts, "created_at": session.created_at, }

@app.get("/sessions")
async def list_sessions():
    return [
        { "id": s.id, "path": s.hosts, "created_at": s.created_at, "last_activity": s.last_activity, }
        for s in sessions.sessions.values()
    ]

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        sessions.get(session_id)
    except KeyError:
        raise HTTPException(404, "Session not found")

    sessions.close(session_id)

    return {"status": "closed"}

@app.websocket("/sessions/{session_id}/terminal")
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
        await asyncio.gather(
            ssh_to_ws(),
            ws_to_ssh(),
        )

    finally:
        sessions.close(session_id)

@app.get("/terminal/{session_id}")
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