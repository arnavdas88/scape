
import time
from typing import List
from dataclasses import asdict, dataclass, field

import paramiko


@dataclass
class SSHCredential:
    username: str
    password: str | None = None
    pkey: paramiko.PKey | None = None

    def to_api(self, ):
        return {
            "username": self.username,
            "auth": "password" if ( self.username and self.password ) else "key"
        }


@dataclass
class SSHHost:
    name: str
    hostname: str
    port: int = 22
    credential: str = ""
    allowed: bool = True

    def to_api(self, ):
        return asdict(self)

@dataclass
class SSHSession:
    id: str
    hosts: List[str]
    client: paramiko.SSHClient
    channel: paramiko.Channel
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    _chain: List[paramiko.SSHClient] = field(default_factory=list)

    def touch(self):
        self.last_activity = time.time()