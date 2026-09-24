import io
import asyncio
from pathlib import Path
from dataclasses import asdict
from contextlib import asynccontextmanager

import paramiko
from pydantic import BaseModel
from fastapi import FastAPI, APIRouter, HTTPException
from scape.server.base import hosts, credentials, sessions
from scape.server.models import SSHCredential, SSHHost, SSHSession
from scape.ssh.utils import detect_key_crypto

management_sub_router = APIRouter(prefix="/v1/management", tags=["Management"])

class CreateCredentials(BaseModel):
    name: str
    username: str
    password: str | None = None
    pkey: str | None = None

class CreateHost(BaseModel):
    name: str
    hostname: str
    port: int = 22
    credential: str | None = None
    allowed: bool = True

class CreateSessionRequest(BaseModel):
    path: list[str]
    term: str = "xterm"
    width: int = 120
    height: int = 40

@management_sub_router.get("/credentials")
def list_credentials():
    return credentials.to_api()

@management_sub_router.post("/credentials")
def create_credentials(req: CreateCredentials):

    if req.password:
        credentials.add( req.name, SSHCredential(username=req.username, password=req.password) )

    elif req.pkey:
        private_key_io = io.StringIO( req.pkey )
        Scheme = detect_key_crypto(private_key_io)
        if not Scheme:
            raise HTTPException(status_code=422, detail="Unable to discern the key type")
        rsa_key_obj = Scheme.from_private_key( private_key_io )
        credentials.add(  req.name, SSHCredential(username=req.username, pkey=rsa_key_obj)  )
    else:
        credentials.add(  req.name, SSHCredential(username=req.username, )  )

    return {"status": "success"}

@management_sub_router.get("/hosts")
def list_hosts():
    return hosts.to_api()

@management_sub_router.post("/hosts")
def create_hosts(req: CreateHost):
    if req.credential and req.credential not in credentials._credentials:
        raise HTTPException(status_code=404, detail="Credential not found")

    hosts.add(
        SSHHost(
            name = req.name,
            hostname = req.hostname,
            port = req.port,
            credential = req.credential,
            allowed = req.allowed,
        )
    )
    
    return {"status": "success"}


@management_sub_router.post("/sessions")
async def create_session(req: CreateSessionRequest):
    try:
        session : SSHSession = await asyncio.to_thread(
            sessions.create_session,
            req.path, req.term, 
            req.width, req.height,
        )

    except Exception as exc:
        raise HTTPException( status_code=400, detail=str(exc), )

    return { "session_id": session.id, "path": session.hosts, "created_at": session.created_at, }

@management_sub_router.get("/sessions")
async def list_sessions():
    return [
        { "id": s.id, "path": s.hosts, "created_at": s.created_at, "last_activity": s.last_activity, }
        for s in sessions.sessions.values()
    ]

@management_sub_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        sessions.get(session_id)
    except KeyError:
        raise HTTPException(404, "Session not found")

    sessions.close(session_id)

    return {"status": "closed"}
