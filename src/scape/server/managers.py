from __future__ import annotations

import asyncio
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from .models import SSHCredential, SSHHost, SSHSession
import paramiko


class CredentialStore:
    def __init__(self):
        self._credentials: dict[str, SSHCredential] = {}

    def add(self, name: str, credential: SSHCredential):
        self._credentials[name] = credential

    def get(self, name: str) -> SSHCredential:
        return self._credentials[name]

class HostStore:
    def __init__(self):
        self._hosts: dict[str, SSHHost] = {}

    def add(self, host: SSHHost):
        self._hosts[host.name] = host

    def get(self, name: str) -> SSHHost:
        host = self._hosts[name]

        if not host.allowed:
            raise PermissionError(f"Host {name} is not allowed")

        return host

class SSHSessionManager:
    def __init__( self, credentials: CredentialStore, hosts: HostStore, ):
        self.credentials = credentials
        self.hosts = hosts

        self.sessions: dict[str, SSHSession] = {}
        self.lock = threading.RLock()

    def _connect( self, host: SSHHost, sock=None, ) -> paramiko.SSHClient:

        credential = self.credentials.get(host.credential)

        client = paramiko.SSHClient()
        # client.set_missing_host_key_policy( paramiko.RejectPolicy() )
        client.set_missing_host_key_policy( paramiko.AutoAddPolicy() )

        client.connect(
            hostname=host.hostname,
            port=host.port,
            username=credential.username,
            password=credential.password,
            pkey=credential.pkey,
            sock=sock,
            timeout=10,
        )

        transport = client.get_transport()

        if transport is None or not transport.is_active():
            # print("SSH transport unavailable")
            client.close()
            raise RuntimeError("SSH transport unavailable")

        return client

    def create_session( self, path: list[str], term: str = "xterm", width: int = 120, height: int = 40, ) -> SSHSession:

        if not path:
            raise ValueError("Empty SSH path")

        clients: list[paramiko.SSHClient] = []

        try:
            previous: Optional[paramiko.SSHClient] = None

            for index, host_name in enumerate(path):
                host = self.hosts.get(host_name)
                # print(f"Connecting to {host}")
                if index == 0:
                    client = self._connect(host)
                else:
                    assert previous is not None
                    transport = previous.get_transport()
                    if transport is None:
                        # print(f"Previous SSH transport ({path[index-1]}) unavailable")
                        raise RuntimeError( "Previous SSH transport unavailable" )

                    # print("direct-tcpip", (host.hostname, host.port), ("", 0))
                    channel = transport.open_channel( "direct-tcpip", (host.hostname, host.port), ("", 0), timeout=10, )

                    client = self._connect( host, sock=channel, )


                # print(f"Connected to {host}: {client.get_transport().is_active()}")

                clients.append(client)
                previous = client

            final_client = clients[-1]

            channel = final_client.invoke_shell( term=term, width=width, height=height, )

            session = SSHSession( id=secrets.token_urlsafe(24), hosts=path, client=final_client, channel=channel, )

            with self.lock:
                self.sessions[session.id] = session

            # Intermediate clients are deliberately retained by the manager
            # through their transport chain. Keep references reachable.
            session._chain = clients

            return session

        except Exception:
            for client in reversed(clients):
                try:
                    client.close()
                except Exception:
                    pass

            raise

    def get(self, session_id: str) -> SSHSession:
        with self.lock:
            return self.sessions[session_id]

    def close(self, session_id: str):
        with self.lock:
            session = self.sessions.pop(session_id, None)

        if not session:
            return

        try:
            session.channel.close()
        except Exception:
            pass

        for client in reversed(session._chain):
            try:
                client.close()
            except Exception:
                pass