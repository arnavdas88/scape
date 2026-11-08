import shlex
import time

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class DependencySpec:
    supported_os: tuple[str, ...] = ("linux",)
    binaries: tuple[str, ...] = ()
    packages: tuple[str, ...] = ()
    verify_packages: bool = False

@dataclass
class CommandSpec:
    command: str
    arguments: tuple[str, ...] = ()

    timeout: int = 30
    sudo: bool = False
    environment: dict[str, str] = field(default_factory=dict)

    dependencies: DependencySpec = field(default_factory=DependencySpec)

    # raw | json | textfsm | auto
    serialization: str = "auto"

    # TextFSM configuration
    template_path: str | Path | None = None
    ntc_platform: str | None = None

    strict_serialization: bool = False
    check_exit_code: bool = True

    @property
    def command_string(self):
        parts = [
            shlex.quote(self.command),
            *(shlex.quote(str(arg)) for arg in self.arguments),
        ]
        return " ".join(parts)

@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    data: Any = None
    serialization: str = "raw"
    execution_time: float = 0.0
    timestamp: float = field(default_factory=time.time)

    @property
    def success(self):
        return self.exit_code == 0

    def as_dict(self):
        return {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "success": self.success,
            "data": self.data,
            "serialization": self.serialization,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
        }
