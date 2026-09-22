
import time
from typing import List
from dataclasses import dataclass, field

import paramiko


@dataclass
class SSHCredential:
    username: str
    password: str | None = None
    pkey: paramiko.PKey | None = None


@dataclass
class SSHHost:
    name: str
    hostname: str
    port: int = 22
    credential: str = ""
    allowed: bool = True


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