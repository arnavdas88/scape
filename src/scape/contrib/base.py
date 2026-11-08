import json
import shlex
import time

from pathlib import Path

import textfsm
from ntc_templates.parse import parse_output

from scape.contrib.models import CommandSpec, DependencySpec, CommandResult
from scape.contrib.exceptions import DependencyError, ExecutionError, SerializationError


def decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value or "")

def remote_execute(session, command, timeout=30, sudo=False):
    """
    Execute a command using the supplied Paramiko/Netmiko
    compatible SSH session.

    Returns:
        stdout, stderr, exit_code
    """

    module = session.conn.__class__.__module__

    if module.startswith("paramiko"):
        _, stdout, stderr = session.exec( command, timeout=timeout, sudo=sudo, )

        output = decode(stdout.read())
        error = decode(stderr.read())
        exit_code = stdout.channel.recv_exit_status()

        return output, error, exit_code

    if module.startswith("netmiko"):
        _, output, error = session.exec( command, timeout=timeout, sudo=sudo, )
        return decode(output), decode(error), 0

    raise ExecutionError( f"Unsupported SSH backend: {module}" )

class DependencyManager:
    @staticmethod
    def verify(session, spec: DependencySpec):
        output, _, code = remote_execute(session, "uname -s")

        if code != 0:
            raise DependencyError("Unable to detect remote OS")

        remote_os = output.strip().lower()

        if remote_os not in spec.supported_os:
            raise DependencyError( f"Unsupported OS: {remote_os}.  Supported: {spec.supported_os}" )

        # Verify required binaries
        for binary in spec.binaries:
            command = f"command -v {shlex.quote(binary)}"
            output, _, code = remote_execute(session, command)

            if code != 0 or not output.strip():
                raise DependencyError( f"Required binary not found: {binary}" )

        # Verify installed packages
        if spec.verify_packages:
            for package in spec.packages:
                DependencyManager.verify_package(session, package)

        return {
            "os": remote_os,
            "binaries": list(spec.binaries),
            "packages": list(spec.packages),
            "verified": True,
        }

    @staticmethod
    def verify_package(session, package):
        package = shlex.quote(package)

        checks = [
            ( "dpkg-query", f"dpkg-query -W -f='${{Status}}' -- {package}", "install ok installed" ),
            ("rpm", f"rpm -q -- {package}", None),
            ("apk", f"apk info -e -- {package}", None),
        ]

        for manager, command, expected in checks:
            _, _, available = remote_execute( session, f"command -v {manager}", )
            if available != 0:
                continue
            output, _, code = remote_execute(session, command)
            if code == 0 and ( expected is None or expected in output ):
                return
            raise DependencyError( f"Required package not installed: {package}" )
        raise DependencyError( f"No supported package manager found for: {package}" )

class OutputSerializer:
    def __init__(self, spec: CommandSpec):
        self.spec = spec

    def serialize(self, output):
        mode = self.spec.serialization.lower()
        if mode == "raw":
            return output, "raw"
        if mode == "json":
            return self.parse_json(output), "json"
        if mode == "textfsm":
            return self.parse_textfsm(output), "textfsm"
        if mode == "auto":
            try:
                return self.parse_json(output), "json"
            except SerializationError:
                pass
            try:
                return self.parse_textfsm(output), "textfsm"
            except Exception:
                if self.spec.strict_serialization:
                    raise
                return output, "raw"
        raise SerializationError( f"Unknown serialization mode: {mode}" )

    @staticmethod
    def parse_json(output):
        try:
            return json.loads(output)
        except (json.JSONDecodeError, TypeError) as exc:
            raise SerializationError( f"Invalid JSON output: {exc}" ) from exc

    def parse_textfsm(self, output):
        if self.spec.template_path:
            path = Path(self.spec.template_path)
            if not path.is_file():
                raise SerializationError( f"Template not found: {path}" )

            with path.open() as file:
                parser = textfsm.TextFSM(file)
                rows = parser.ParseText(output)

            return [ dict(zip(parser.header, row)) for row in rows ]

        if not self.spec.ntc_platform:
            raise SerializationError( "NTC platform is required" )

        return parse_output(
            platform=self.spec.ntc_platform,
            command=self.spec.command_string,
            data=output,
        )

class RemoteCommand:
    """
    Base class for all remote commands.

    Subclasses only need to implement configure().
    """

    def __init__(self, **config):
        self.spec = self.configure(**config)
        if not isinstance(self.spec, CommandSpec):
            raise TypeError( "configure() must return CommandSpec" )
        self.serializer = OutputSerializer(self.spec)

    def configure(self, **config):
        raise NotImplementedError

    # Optional lifecycle hooks

    def pre_execute(self, session):
        pass

    def post_execute(self, result: CommandResult):
        pass

    def build_command(self):
        command = self.spec.command_string
        if self.spec.environment:
            env = " ".join( shlex.quote(f"{key}={value}") for key, value in self.spec.environment.items() )
            command = f"env {env} {command}"
        return command

    def execute(self, session):

        self.pre_execute(session)

        # 1. Verify dependencies
        dependency_info = DependencyManager.verify( session, self.spec.dependencies, )
        # 2. Build command
        command = self.build_command()
        # 3. Execute remotely
        start = time.monotonic()
        stdout, stderr, exit_code = remote_execute( session, command, timeout=self.spec.timeout, sudo=self.spec.sudo, )
        elapsed = time.monotonic() - start
        # 4. Check execution status
        if self.spec.check_exit_code and exit_code != 0:
            raise ExecutionError( f"Command failed ({exit_code}): " f"{command}\n{stderr or stdout}" )
        # 5. Serialize output
        try:
            data, serialization = self.serializer.serialize(stdout)
        except Exception:
            if self.spec.strict_serialization:
                raise
            data = stdout
            serialization = "raw"
        # 6. Construct result
        result = CommandResult(
            command=command,
            stdout=stdout, stderr=stderr, exit_code=exit_code,
            data=data, serialization=serialization,
            execution_time=elapsed,
        )

        self.post_execute(result)

        return result

    def __call__(self, session):
        return self.execute(session)
